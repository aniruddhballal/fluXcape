# Magnetofrictional Model and Possible Research Directions

## Project 1: Develop a magnetofrictional model

The immediate priority, as described by Prantika, is to develop a **magnetofrictional model** of the solar coronal magnetic field. The starting reference is [Anthony Yeates's introduction to magnetofrictional modelling](https://www.maths.dur.ac.uk/users/anthony.yeates/highlights/mf.html).

A magnetofrictional model evolves the magnetic field using an artificial relaxation velocity, allowing the field to move toward force-free states while responding to boundary driving. The linked global model also includes surface magnetic-field evolution and an outer solar-wind outflow. The exact scope, geometry, starting code, numerical methods and intended applications of this project are still to be discussed with Prantika.

An initial goal is to understand the physical assumptions and numerical methods, develop the model in the agreed scope, and verify it against suitable test cases or published results. The choice of programming language should follow the project's requirements and the group's existing code.

## Possible follow-on research

The following are ideas for discussion, not confirmed project objectives. Their feasibility depends on what the model can represent and on the direction agreed with Prantika.

### 2. Confined and eruptive events

Can the model help identify differences in magnetic structure or evolution associated with confined and eruptive events? This could involve comparing modelled magnetic configurations and appropriate diagnostics with observations or established studies.

### 3. The role of spatial scale

How sensitive are those modelled structures and diagnostics to the spatial detail in the magnetic boundary input? For example, one could compare otherwise consistent model runs using filtered or lower-resolution magnetic maps. This would test how much detail is needed for a particular diagnostic or comparison, rather than assume a universal minimum scale.

The original research question combines these two ideas: **Which spatial scales and topological features of pre-eruption magnetic fields are necessary to distinguish confined from eruptive events, and how robust are the inferred diagnostics when small-scale magnetic information is removed?** It remains a possible longer-term question, not a commitment or an established research gap.

## Modelling limits

Magnetofriction is useful for studying slowly evolving coronal magnetic configurations and can exhibit eruptive behaviour. Its relaxation velocity is artificial, however, so it does not reproduce the full fast plasma dynamics of an eruption. Any comparison with observed events and any claim about stability or prediction must account for the model's assumptions, boundary inputs and validation. A potential-field extrapolation may also be useful as a simpler baseline, but cannot represent the full current-carrying structure.
