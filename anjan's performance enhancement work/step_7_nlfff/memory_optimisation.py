"""Preserve WSR expressions; release dead temporaries and cache constant gradients."""
import ast
import copy


def reads(node):
    result = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    for n in ast.walk(node):
        if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            result.add(n.target.id)
    return result


def defines(node):
    if isinstance(node, ast.Assign):
        return {n.id for t in node.targets for n in ast.walk(t)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    if isinstance(node, (ast.AugAssign, ast.AnnAssign)) and isinstance(node.target, ast.Name):
        return {node.target.id}
    return set()


def release_dead(body, live_end):
    """Conservative straight-line liveness; conditional assignments are not kills."""
    eligible = set().union(*(defines(n) for n in body))
    eligible = {name for name in eligible if not name.startswith('_')}
    live = set(live_end)
    after = []
    for node in reversed(body):
        after.append(set(live))
        live = (live - defines(node)) | reads(node)
    result = []
    for node, live_after in zip(body, reversed(after)):
        result.append(node)
        dead = (defines(node) | reads(node)) & eligible - live_after
        if dead and not isinstance(node, (ast.Return, ast.Raise)):
            result.append(ast.Delete(targets=[ast.Name(id=name, ctx=ast.Del()) for name in sorted(dead)]))
    return result, live


def strip_deletes(tree):
    class Strip(ast.NodeTransformer):
        def visit_Delete(self, node):
            return None
    return Strip().visit(copy.deepcopy(tree))


def optimise_wsr(source):
    tree = ast.parse(source)
    original = ast.dump(tree)
    loops = [n for n in tree.body if isinstance(n, ast.While)]
    if len(loops) != 1:
        raise ValueError('Expected exactly one reconstruction loop')
    loop = loops[0]
    index = tree.body.index(loop)
    gradients = [n for n in loop.body if defines(n) & {'gradw_x', 'gradw_y', 'gradw_z'}]
    gradient_positions = [loop.body.index(n) for n in gradients]
    if len(gradients) != 3:
        raise ValueError('Expected three unchanged weight-gradient expressions')
    # Reject source variants that mutate the cached gradient inputs in the loop.
    for node in ast.walk(loop):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in {'w', 'X1', 'Y1', 'Z1'}:
            raise ValueError('Weight/grid mutation prevents invariant caching')
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) and node.value.id in {'w', 'X1', 'Y1', 'Z1'}:
            raise ValueError('Weight/grid mutation prevents invariant caching')
    prefix, suffix = tree.body[:index], tree.body[index+1:]
    after_loop = set().union(*(reads(n) for n in suffix)) if suffix else set()
    # Find names needed on entry and on following iterations, respecting stores.
    _, entry = release_dead(loop.body, after_loop | reads(loop.test))
    loop.body, _ = release_dead(loop.body, entry | after_loop | reads(loop.test))
    # Original arithmetic must remain unchanged before relocating invariants.
    if ast.dump(strip_deletes(tree)) != original:
        raise AssertionError('Lifetime optimisation changed original statements')
    loop.body = [n for n in loop.body if n not in gradients]
    # These invariants must survive across all iterations and their original uses.
    for node in loop.body:
        if isinstance(node, ast.Delete):
            node.targets = [t for t in node.targets if t.id not in {'gradw_x', 'gradw_y', 'gradw_z'}]
    loop.body = [n for n in loop.body if not isinstance(n, ast.Delete) or n.targets]
    prefix, _ = release_dead(prefix + gradients, entry | after_loop | reads(loop.test) |
                             {'gradw_x', 'gradw_y', 'gradw_z'})
    tree.body = prefix + [loop] + suffix
    restored = strip_deletes(tree)
    restored.body = [n for n in restored.body if not (defines(n) & {'gradw_x', 'gradw_y', 'gradw_z'})]
    restored_loop = next(n for n in restored.body if isinstance(n, ast.While))
    for position, gradient in zip(gradient_positions, gradients):
        restored_loop.body.insert(position, copy.deepcopy(gradient))
    if ast.dump(restored) != original:
        raise AssertionError('Caching changed more than the invariant statement locations')
    return ast.unparse(ast.fix_missing_locations(tree)) + '\n'


def optimise_vector_math(source):
    tree = ast.parse(source)
    original = ast.dump(tree)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in {'curl_scipy', 'compute_divergence_nonuniform'}:
            node.body, _ = release_dead(node.body, set())
    if ast.dump(strip_deletes(tree)) != original:
        raise AssertionError('Vector-helper optimisation changed original statements')
    return ast.unparse(ast.fix_missing_locations(tree)) + '\n'
