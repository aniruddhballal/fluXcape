/*
 * Magnetogram preprocessing
 * Adapted from Wiegelmann's prepro.c
 * Takes in bz0 magnetogram
 * Computes and outputs processed mag
 * Adapted by X. Sun
 * Version 1.0 Mar 21 2010
 *  Parameters needs to be tweaked
 */



// mu1 = 1.0; mu2 = 1.0; mu3 = 0.001; mu4 = 0.01; mu5 = 0.0;
// maxit = 10000;
#include <stdio.h>   // for printf, FILE, fopen, fprintf, fclose
#include <stdlib.h>  // for malloc, calloc, free, exit, NULL
#include <math.h>    // for sqrt, fabs

void preproc(double *Bx, double *By, double *Bz, 
             int nx, int ny, 
             double mu1, double mu2, double mu3, double mu4, double mu5, 
             int maxit, int verb)
{
	FILE *streamw;
    double *x, *y, *r;
    double *Bxo, *Byo, *Bzo;
    double *Bx1, *By1, *Bz1;
    double *LapBx, *LapBy, *LapBz;
    double *term3a, *term3b, *term3c;
    double *term4a, *term4b, *term4c;
    double Bave, dt;
    double dx, dy, dxdy;
    double Emag, ihelp;
    double dL, L, L1, L2, L12, L3, L4, L5;
    double oldL12, oldL3, oldL4, oldL5, oldL;
    double dL12, dL3, dL4, dL5;
    double term1a, term1b, term1c, term1c1, term1c2; 
    double term2a, term2b, term2c;
    double term2a1, term2a2, term2b1, term2b2, term2c1, term2c2;
    double term5;
    int nxny;
    int i, ix, iy, it;
    int i1, i2, ix1, iy1;
    int i3, i4, ix2, iy2;

    nxny = nx * ny;

    LapBx = (double *) calloc(nxny, sizeof(double));
    LapBy = (double *) calloc(nxny, sizeof(double));
    LapBz = (double *) calloc(nxny, sizeof(double));
    Bx1 = (double *) calloc(nxny, sizeof(double));
    By1 = (double *) calloc(nxny, sizeof(double));
    Bz1 = (double *) calloc(nxny, sizeof(double));
    Bxo = (double *) calloc(nxny, sizeof(double));
    Byo = (double *) calloc(nxny, sizeof(double));
    Bzo = (double *) calloc(nxny, sizeof(double));
    x = (double *) calloc(nx, sizeof(double));
    y = (double *) calloc(ny, sizeof(double));
    r = (double *) calloc(nxny, sizeof(double));
    term3a = (double *) calloc(nxny, sizeof(double));
    term3b = (double *) calloc(nxny, sizeof(double));
    term3c = (double *) calloc(nxny, sizeof(double));
    term4a = (double *) calloc(nxny, sizeof(double));
    term4b = (double *) calloc(nxny, sizeof(double));
    term4c = (double *) calloc(nxny, sizeof(double));

    if (verb) printf("Raw vectormagnetogram loaded \n");
    Bave = 0.0;
#ifdef _OPENMP
#pragma omp parallel for private (i,ix,iy) reduction(+:Bave)
#endif
    for (ix = 0; ix < nx; ix++)
    for (iy = 0; iy < ny; iy++) {
        i = ny * ix + iy;
        Bave = Bave + sqrt(Bx[i] * Bx[i] + By[i] * By[i] + Bz[i] * Bz[i]);
    }
    Bave = Bave / nx / ny;

#ifdef _OPENMP
#pragma omp parallel for private (i)
#endif
    for (i = 0; i < nxny; i++) {
        Bx[i] = Bx1[i] = Bxo[i] = Bx[i] / Bave;
        By[i] = By1[i] = Byo[i] = By[i] / Bave;
        Bz[i] = Bz1[i] = Bzo[i] = Bz[i] / Bave;
    }
    dx = 1.0 / (nx - 1); dy = 1.0 / (ny - 1);
    dxdy = dx * dy;
    for (ix = 0; ix < nx; ix++) x[ix] = ix * dx;
    for (iy = 0; iy < ny; iy++) y[iy] = iy * dy;

#ifdef _OPENMP
#pragma omp parallel for private (i,ix,iy)
#endif
    for (ix = 0; ix < nx; ix++)
    for (iy = 0; iy < ny; iy++) {
        i = ny * ix + iy;
        r[i] = sqrt(x[ix] * x[ix] + y[iy] * y[iy]);
    }

    /* Do the Preprocessing */
    dt = 0.01;
    Emag = ihelp = 0.0;
#ifdef _OPENMP
#pragma omp parallel for private (i) reduction(+:Emag) reduction(+:ihelp)
#endif
    for (i = 0; i < nxny; i++) {
        Emag = Emag + (Bx[i] * Bx[i] + By[i] * By[i] + Bz[i] * Bz[i]);
        ihelp = ihelp + (r[i] * (Bx[i] * Bx[i] + By[i] * By[i] + Bz[i] * Bz[i]));
    }
    /*************************************/
    /********** Start Iteration **********/
    /*************************************/
    L = 10.0; dL=1.0; oldL=10.0;
    it = -1;
    while(it < maxit && dL > 0.0001 && dt > 1.0e-6)
    {
        it++;
        term1a = term1b = term1c = term1c1 = term1c2 = 0.0;
        term2a = term2b = term2c = 0.0;
        term2a1 = term2b1 = term2c1 = 0.0;
        term2a2 = term2b2 = term2c2 = 0.0;
        L1 = L2 = L3 = L4 = L5 = 0.0;
#ifdef _OPENMP
#pragma omp parallel for private (i,ix,iy) reduction(+:term1a) reduction(+:term1b) reduction(+:term1c1) reduction(+:term1c2) reduction(+:term2a1) reduction(+:term2a2) reduction(+:term2b1) reduction(+:term2b2) reduction(+:term2c1) reduction(+:term2c2) reduction(+:L3)
#endif
        for (ix = 0; ix < nx; ix++)
        for (iy = 0; iy < ny; iy++)
        {
            i = ny * ix + iy;
            /********** Term 1 Force **********/
            term1a = term1a + Bx[i] * Bz[i];
            term1b = term1b + By[i] * Bz[i];
            term1c1 = term1c1 + Bz[i] * Bz[i];
            term1c2 = term1c2 + Bx[i] * Bx[i] + By[i] * By[i];
            /********** Term 2 Torque **********/
            term2a1 = term2a1 + x[ix] * Bz[i] * Bz[i];
            term2a2 = term2a2 + x[ix] * (Bx[i] * Bx[i] + By[i] * By[i]);
            term2b1 = term2b1 + y[iy] * Bz[i] * Bz[i];
            term2b2 = term2b2 + y[iy] * (Bx[i] * Bx[i] + By[i] * By[i]);
            term2c1 = term2c1 + y[iy] * Bx[i] * Bz[i];
            term2c2 = term2c2 + x[ix] * By[i] * Bz[i];
            /********** Term 3 Data **********/
            term3a[i] = (Bx[i] - Bxo[i]) * (Bx[i] - Bxo[i]) / Emag;
            term3b[i] = (By[i] - Byo[i]) * (By[i] - Byo[i]) / Emag;
            term3c[i] = (Bz[i] - Bzo[i]) * (Bz[i] - Bzo[i]) / Emag;
            L3 = L3 + term3a[i] + term3b[i] + term3c[i];
        }
        term1a = term1a / Emag;
        term1b = term1b / Emag;
        term1c = (term1c1 - term1c2) / Emag;
        term2a = (term2a1 - term2a2) / ihelp;
        term2b = (term2b1 - term2b2) / ihelp;
        term2c = (term2c1 - term2c2) / ihelp;
        L1 = term1a * term1a + term1b * term1b + term1c * term1c;
        L2 = term2a * term2a + term2b * term2b + term2c * term2c;
        L12 = L1 + L2;
        L3 = L3 / Emag;
        /********** Laplace Bx,By,Bz **********/
#ifdef _OPENMP
#pragma omp parallel for private (i,ix,iy,ix1,ix2,iy1,iy2,i1,i2,i3,i4) reduction(+:L4)
#endif
        for (ix = 0; ix < nx; ix++)
        for (iy = 0; iy < ny; iy++)
        {
            i = ny * ix + iy;
            ix1 = ix + 1; if (ix1 == nx) ix1 = 0;
            ix2 = ix - 1; if (ix2 == -1) ix2 = nx - 1;
            iy1 = iy + 1; if (iy1 == ny) iy1 = 0;
            iy2 = iy - 1; if (iy2 == -1) iy2 = ny - 1;
            i1 = ny * ix1 + iy;
            i2 = ny * ix2 + iy;
            i3 = ny * ix + iy1;
            i4 = ny * ix + iy2;
            LapBx[i] = -4 * Bx[i] + Bx[i1] + Bx[i2] + Bx[i3] + Bx[i4];
            LapBy[i] = -4 * By[i] + By[i1] + By[i2] + By[i3] + By[i4];
            LapBz[i] = -4 * Bz[i] + Bz[i1] + Bz[i2] + Bz[i3] + Bz[i4];
            L4 = L4 + LapBx[i] * LapBx[i] + LapBy[i] * LapBy[i] + LapBz[i] * LapBz[i];
        }
        L4 = dxdy * L4 / Emag;
        L = mu1 * L1 + mu2 * L2 + mu3 * L3 + mu4 * L4 + mu5 * L5;
        /********** Term 4 Smoothing **********/
#ifdef _OPENMP
#pragma omp parallel for private (i,ix,iy,ix1,ix2,iy1,iy2,i1,i2,i3,i4)
#endif
        for(ix = 0; ix < nx; ix++)
        for(iy = 0; iy < ny; iy++)
        {
            i = ny * ix + iy;
            ix1 = ix + 1; if (ix1 == nx) ix1 = 0;
            ix2 = ix - 1; if (ix2 == -1) ix2 = nx - 1;
            iy1 = iy + 1; if (iy1 == ny) iy1 = 0;
            iy2 = iy - 1; if (iy2 == -1) iy2 = ny - 1;
            i1 = ny * ix1 + iy;
            i2 = ny * ix2 + iy;
            i3 = ny * ix + iy1;
            i4 = ny * ix + iy2;
            term4a[i] = - 8 * LapBx[i] + 2 * LapBx[i1] 
                        + 2 * LapBx[i2] + 2 * LapBx[i3] + 2 * LapBx[i4];
            term4b[i] = - 8 * LapBy[i] + 2 * LapBy[i1] 
                        + 2 * LapBy[i2] + 2 * LapBy[i3] + 2 * LapBy[i4];
            term4c[i] = - 8 * LapBz[i] + 2 * LapBz[i1] 
                        + 2 * LapBz[i2] + 2 * LapBz[i3] + 2 * LapBz[i4];
        }
        if (it > 0) {
            dL12 = dL3 = dL4 = dL5 = 0.0;
            if (L12 != 0.0) dL12 = fabs(L12 - oldL12) / L12;
            if (L3 != 0.0) dL3 = fabs(L3 - oldL3) / L3;
            if (L4 != 0.0) dL4 = fabs(L4 - oldL4) / L4;
            if (L5 != 0.0) dL5 = fabs(L5 - oldL5) / L5;
            if (L != 0.0) dL = (oldL - L) / L;
        }
        if (it % 100 == 0 && verb == 2) {
            printf("%i L12= %lf, L3= %lf, L4= %lf, L=%lf, dL= %lf\n", 
            it, 1.0e6*L12, 1.0e6*L3, 1.0e6*L4, 1.0e6*L, dL);
        }
        if(oldL < L && it > 0) {
            dt = dt / 2;
            if (verb == 2) printf("dt reduced: %i, dt=%lf, dL=%lf, oldL=%lf, L=%lf\n",
            it, dt, dL, 1.0e6*oldL, 1.0e6*L);
            dL = 1.0;
            oldL = L;
        } else {
            if (it > 0) dt = dt * 1.001;
            oldL12 = L12; oldL3 = L3;
            oldL4 = L4; oldL5 = L5;
            oldL = L;
        }
        /********** Iterate for new B **********/
#ifdef _OPENMP
#pragma omp parallel for private (i,ix,iy)
#endif
        for (ix = 0; ix < nx; ix++)
        for (iy = 0; iy < ny; iy++)
        {
            i = ny * ix + iy;
            Bx1[i] = Bx[i] + dt * 
                     (mu1 * (-2 * term1a * Bz[i] + 4 * term1c * Bx[i])
                      - mu3 * 2 * (Bx[i] - Bxo[i])
                      - mu4 * term4a[i]
                      + mu2 * 
                          (4 * term2a * x[ix] * Bx[i] + 4 * term2b * y[iy] * Bx[i] 
                           - 2 * term2c * y[iy] * Bz[i]));
            By1[i] = By[i] + dt * 
                     (mu1 * (-2 * term1b * Bz[i] + 4 * term1c * By[i])
                      - mu3 * 2 * (By[i] - Byo[i])
                      - mu4 * term4b[i]
                      + mu2 * 
                          (4 * term2a * x[ix] * By[i] + 4 * term2b * y[iy] * By[i]
                           + 2 * term2c * x[ix] * Bz[i]));
            Bz1[i] = Bz[i] + dt * (- mu3 * 2 * (Bz[i] - Bzo[i]) - mu4 * term4c[i]);
        }
        /********** Update B **********/
#ifdef _OPENMP
#pragma omp parallel for private (i)
#endif
        for (i = 0; i < nxny; i++) {
            Bx[i] = Bx1[i];
            By[i] = By1[i];
            Bz[i] = Bz1[i];
        }

    } /*End of Iteration*/
    
    if (verb) printf("End of Iteration\n");
    if (verb == 2) {
        printf("mu3= %lf \t mu4= %lf \t mu5= %lf\n", mu3, mu4, mu5);
        printf("%i L12= %lf, L3= %lf, L4= %lf, L=%lf, dL= %lf\n", 
        it, 1.0e6*L12, 1.0e6*L3, 1.0e6*L4, 1.0e6*L,dL);
    }
    
    /* Output data */
#ifdef _OPENMP
#pragma omp parallel for private (i)
#endif
    for (i = 0; i < nxny; i++) {
        Bx[i] = Bx[i] * Bave;
        By[i] = By[i] * Bave;
        Bz[i] = Bz[i] * Bave;
	 }

	if((streamw = fopen("Bpre.dat","w")) == NULL) { printf("\n Error Bpre.dat"); exit(1);}
	for(iy=0;iy<ny;iy++)
	for(ix=0;ix<nx;ix++)
	 {
	  i=ny*ix+iy;
	  fprintf(streamw,"%lf\n %lf\n %lf\n",Bx[i],By[i],Bz[i]);
	 }
	fclose(streamw);
	printf("\n Preprocessed B written to Bpre.dat \n");
    
    /* Clean up */
    free(LapBx); free(LapBy); free(LapBz);
    free(Bx1); free(By1); free(Bz1);
    free(Bxo); free(Byo); free(Bzo);
   free(x); free(y); free(r);
    free(term3a); free(term3b); free(term3c);
    free(term4a); free(term4b); free(term4c);

}


#include <stdio.h>
#include <stdlib.h>

void load_field_with_coords(const char *filename, double *Bx, double *X, double *Y, int Nx, int Ny) {
    FILE *f = fopen(filename, "r");
    if (!f) {
        fprintf(stderr, "Error opening %s\n", filename);
        exit(1);
    }

    for (int j = 0; j < Ny; j++) {
        for (int i = 0; i < Nx; i++) {
            int idx = i + Nx * j;
            if (fscanf(f, "%lf %lf %lf", &X[idx], &Y[idx], &Bx[idx]) != 3) {
                fprintf(stderr, "Error reading data at %d %d\n", i, j);
                exit(1);
            }
        }
    }
    fclose(f);
}

int main() {
    int Nx = 300;
    int Ny = 300;

    double *Bx = malloc(Nx * Ny * sizeof(double));
    double *By = malloc(Nx * Ny * sizeof(double));
    double *Bz = malloc(Nx * Ny * sizeof(double));
    double *X  = malloc(Nx * Ny * sizeof(double));
    double *Y  = malloc(Nx * Ny * sizeof(double));

    if (!Bx || !By || !Bz || !X || !Y) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    // Load X, Y coordinates only once (they are same across Bx, By, Bz files)
    load_field_with_coords("interpolated_dataBx.dat", Bx, X, Y, Nx, Ny);

    // Load only field values for By and Bz
    {
        FILE *f = fopen("interpolated_dataBy.dat", "r");
        for (int j = 0; j < Ny; j++) {
            for (int i = 0; i < Nx; i++) {
                int idx = i + Nx * j;
                double x, y;
                fscanf(f, "%lf %lf %lf", &x, &y, &By[idx]);
            }
        }
        fclose(f);
    }
    {
        FILE *f = fopen("interpolated_dataBz.dat", "r");
        for (int j = 0; j < Ny; j++) {
            for (int i = 0; i < Nx; i++) {
                int idx = i + Nx * j;
                double x, y;
                fscanf(f, "%lf %lf %lf", &x, &y, &Bz[idx]);
            }
        }
        fclose(f);
    }

    // --- Call preprocessing ---
    preproc(Bx, By, Bz, Nx, Ny, 1.0, 1.0, 0.001, 0.01, 0.0, 10000, 3);

    // --- Save processed field with correct coordinates ---
    FILE *fout = fopen("Bfield_processed.dat", "w");
    for (int j = 0; j < Ny; j++) {
        for (int i = 0; i < Nx; i++) {
            int idx = i + Nx * j;
            fprintf(fout, "%.6f %.6f %.6e %.6e %.6e\n",
                    X[idx], Y[idx], Bx[idx], By[idx], Bz[idx]);
        }
    }
    fclose(fout);

    free(Bx); free(By); free(Bz); free(X); free(Y);
    return 0;
}

