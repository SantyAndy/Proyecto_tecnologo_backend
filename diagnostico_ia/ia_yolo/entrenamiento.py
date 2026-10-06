"""
============================================================================
  ENTRENAMIENTO DEL MODELO YOLOv8  —  (ESTA PARTE LA HACES TÚ)
============================================================================

Aquí entrenas tu modelo. El backend NO toca esto; solo usa los pesos que
generes (guárdalos en `pesos_entrenados/best.pt`).

Ejemplo de referencia con ultralytics:

    from ultralytics import YOLO

    def entrenar():
        modelo = YOLO('yolov8n.pt')            # modelo base
        modelo.train(
            data='dataset/data.yaml',          # tu dataset (Roya, Ojo de Gallo, etc.)
            epochs=100,
            imgsz=640,
            project='diagnostico_ia/ia_yolo',
            name='pesos_entrenados',
        )

Clases sugeridas para el dataset: roya, ojo_de_gallo, deficiencia, sano.
"""


def entrenar_modelo():
    """TODO (TÚ): implementa el entrenamiento de YOLOv8."""
    raise NotImplementedError('Implementa aquí el entrenamiento de tu modelo YOLOv8.')
