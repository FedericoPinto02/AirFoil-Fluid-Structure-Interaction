import gmsh
import numpy as np
import meshio
from dolfinx import mesh, io, plot
from mpi4py import MPI
import pyvista
import sys

# --- 1. Parametri e Inizializzazione ---

# --- Nome del file STEP aggiornato ---
step_filename = "cadFiles/NASAsc2-0410.STEP"
# -----------------------------------

lc_mesh = 0.3      # Dimensione della mesh (più piccolo = più fine = più lento)
                    # NOTA: 0.01 potrebbe essere TROPPO fine per questo modello
output_msh = "solid_mesh_from_step.msh"
output_xdmf = "solid_mesh_from_step.xdmf"

# --- 2. Creazione della Mesh 3D SOLIDA da file .STEP ---

gmsh.initialize()
gmsh.model.add("solid_from_step")

# Prova a importare il file STEP
try:
    gmsh.model.occ.importShapes(step_filename)
except Exception as e:
    print(f"Errore durante l'importazione del file STEP: {e}")
    print(f"Assicurati che il file '{step_filename}' sia nella stessa cartella.")
    gmsh.finalize()
    sys.exit()

# --- CORREZIONE: Usa la sincronizzazione OCC (OpenCASCADE) ---
gmsh.model.occ.synchronize()
# --------------------------------------------------------

# --- LOGICA MIGLIORATA: Cerca volumi o crea un volume da superfici ---
volumes = gmsh.model.occ.getEntities(3)
if volumes:
    print(f"Trovati {len(volumes)} volumi nel file STEP. Avvio meshing del volume.")
else:
    # Se non ci sono volumi, forse è solo un modello di superficie
    surfaces = gmsh.model.occ.getEntities(2)
    if surfaces:
        print(f"Trovate {len(surfaces)} superfici, ma nessun volume.")
        print("Provo a creare un volume da queste superfici (potrebbe richiedere tempo)...")
        
        surface_tags = [s[1] for s in surfaces]
        # Prova a "cucire" le superfici
        gmsh.model.occ.sew(surfaces)
        
        # Crea un 'surface loop' (guscio)
        shell = gmsh.model.geo.addSurfaceLoop(surface_tags)
        
        # Prova a creare un volume da questo guscio
        try:
            volume = gmsh.model.geo.addVolume([shell])
            gmsh.model.geo.synchronize()
            print(f"Creato volume {volume} dal guscio di superficie.")
        except Exception as e:
            print(f"Errore: Impossibile creare un volume dal guscio di superficie. {e}")
            print("Il file STEP potrebbe non essere un guscio chiuso ('water-tight').")
            gmsh.finalize()
            sys.exit()
    else:
        # SE ANCHE QUESTO FALLISCE, allora l'errore è reale.
        print("Errore: Nessun volume E nessuna superficie trovati nel file STEP importato.")
        gmsh.finalize()
        sys.exit()

# --- CORREZIONE: Applica la dimensione della mesh in modo robusto ---
# Applica la dimensione mesh a tutti i punti del modello
all_points = gmsh.model.occ.getEntities(0)
gmsh.model.mesh.setSize(all_points, lc_mesh)
# ------------------------------------------------------------

# Sincronizza di nuovo
gmsh.model.occ.synchronize()

# Genera la mesh 3D (tetraedri)
print("Avvio generazione mesh 3D (può richiedere tempo)...")
gmsh.model.mesh.generate(3)
print("Generazione mesh completata.")

# Salva la mesh 3D
gmsh.write(output_msh)
gmsh.finalize()

print(f"Mesh '{output_msh}' creata con successo.")

# --- 3. Caricamento della Mesh 3D in FEniCSx ---

msh = meshio.read(output_msh)

# --- FILTRO 3D (per l'errore "mixed") ---
# Filtriamo per tenere solo gli elementi 3D (tetraedri)
cells_3d = []
for cell_block in msh.cells:
    if cell_block.type in ["tetra", "tetra10"]: # Supporta tetra lineari e quadratici
        cells_3d.append(cell_block)

if not cells_3d:
    print(f"Errore: Nessun elemento 'tetra' trovato nel file '{output_msh}'.")
    print("Possibili tipi di celle trovati:")
    for cell_block in msh.cells:
        print(f"- {cell_block.type}")
    sys.exit()

# Crea una nuova mesh meshio contenente *solo* i punti e le celle 3D
filtered_mesh = meshio.Mesh(
    points=msh.points,
    cells=cells_3d
)
# --- FINE FILTRO 3D ---

# Scrive la mesh 3D filtrata in XDMF
filtered_mesh.write(output_xdmf)

# In FEniCSx, leggiamo la mesh 3D
with io.XDMFFile(MPI.COMM_WORLD, output_xdmf, "r") as xdmf:
    domain = xdmf.read_mesh(name="Grid")

print(f"Mesh 3D SOLIDA caricata in FEniCSx. Dimensione topologica: {domain.topology.dim}")
print(f"Numero di celle (3D): {domain.topology.index_map(domain.topology.dim).size_global}")
print(f"Numero di vertici: {domain.topology.index_map(0).size_global}")


# --- 4. Visualizzazione con PyVista ---

p = pyvista.Plotter(window_size=[1024, 768])

# Converti la mesh DOLFINx 3D per PyVista
topology, cell_types, geometry = plot.vtk_mesh(domain, domain.topology.dim)
grid = pyvista.UnstructuredGrid(topology, cell_types, geometry)

# Aggiungi la mesh 3D al plotter
p.add_mesh(grid, show_edges=True, color="silver", opacity=1.0) 

# Mostra gli assi
p.show_axes()

# Mostra il plotter
if not pyvista.OFF_SCREEN:
    p.show()
else:
    figure_as_array = p.screenshot("solid_mesh_from_step.png")