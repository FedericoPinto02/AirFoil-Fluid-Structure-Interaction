# 3D Fluid-Structure Interaction Simulation of NASA SC(2)-0410 Airfoil

This repository contains the computational setup and documentation for the 3D Fluid-Structure Interaction (FSI) simulation of a deformable wing based on the NASA SC(2)-0410 airfoil. The project was developed within the High Performance Simulation Lab for Mechanical Engineering at Politecnico di Milano.

## 📄 Project Documentation

For a comprehensive explanation of the theoretical background, numerical methods, mesh generation, scalability analysis, and validation results, please consult the official project report:

👉 **[Read the full report](./Report_HPC4MEC.pdf)**

## 🔬 Project Overview

This project investigates the mutual effects between a deformable structure and a surrounding fluid. To handle the high complexity of the coupled phenomena in a 3D configuration, the simulation employs a high-fidelity partitioned approach managed by an implicit coupling scheme. 

The main software stack consists of:
* **Fluid Domain**: OpenFOAM (v2306) is used to solve the incompressible Navier-Stokes equations in an Arbitrary Lagrangian-Eulerian (ALE) frame.
* **Solid Domain**: FEniCS is used to model the wing as a linear elastic material, corresponding to a standard aeronautical aluminum alloy.
* ]**Coupling Library**: preCICE is utilized to manage the bidirectional exchange of forces and displacements across the non-conformal fluid-solid interfaces using Radial Basis Function (RBF) mapping.

## 👥 Authors

* Mattia Gotti
* Michele Milani
* Stefano Pedretti
* Federico Pinto

## 🐳 Environment Setup (Docker)

To manage the complex and conflicting dependencies of OpenFOAM, FEniCS, and preCICE (such as different MPI versions and Python environments), the entire computational workflow has been containerized. 

Inside this repository, you will find a `.zip` archive containing the required Dockerfiles to create the environment via `docker-compose`. This setup creates two specialized, independent containers (Fluid Participant and Solid Participant) that communicate over a dedicated bridge network.

### ⚠️ Important Hardware & Configuration Adjustments

Since this project relies on a complex containerized architecture, **you may need to tweak the setup depending on your specific host machine**:

1.  **Docker & Docker Compose**: Depending on your operating system (Windows/macOS/Linux) and underlying architecture (e.g., ARM vs x86), you might need to make local adjustments to the provided Dockerfiles or the `docker-compose.yml` file to ensure the containers build and run correctly.
2.  **preCICE Configuration (`precice-config.xml`)**: The simulation workflow and communication protocols are defined in the `precice-config.xml` file[cite: 275]. Because network interfaces and socket bindings can behave differently across various host setups, you may need to adjust the `<m2n:sockets>` tags or the network attributes (e.g., `network="eth0"`) to match your local Docker bridge network configuration.

## 🚀 Execution

Once the Docker Compose environment is successfully built and adapted to your machine, the synchronization between the two solver containers is handled automatically. The OpenFOAM fluid solver and the FEniCS structural solver will interact over the network as disjoint memory spaces, iterating within each time window until sub-cycling convergence is achieved.
