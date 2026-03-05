try:
    from moviepy.editor import *
    print("MoviePy importé avec succès!")
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    import sys
    print(f"Python path: {sys.path}")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}") 