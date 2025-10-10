import os, stat, shutil
import sys
import subprocess
from pathlib import Path
import time
import math
import json
import datetime
import cv2
import numpy as np
import argparse
# from kivy.clock import Clock # COMMENTÉ: Remplacé par un appel direct pour CLI

# --- Variables Globales ---
if getattr(sys, 'frozen', False):
    # Exécuté en tant que bundle PyInstaller
    base_path = sys._MEIPASS
else:
    # Exécuté dans un environnement Python normal
    base_path = os.path.dirname(os.path.abspath(__file__))
    
# Assurez-vous que le répertoire 'data/images' existe par rapport à base_path
images_path = os.path.join(base_path, 'data', 'images')
hand_path = os.path.join(images_path, 'drawing-hand.png')
hand_mask_path = os.path.join(images_path, 'hand-mask.png')
save_path = os.path.join(base_path, "save_videos")
platform = "linux"

# --- Classes et Fonctions ---

def euc_dist(arr1, point):
    """Calcule la distance euclidienne entre un tableau de points (arr1) et un seul point."""
    square_sub = (arr1 - point) ** 2
    return np.sqrt(np.sum(square_sub, axis=1))

def preprocess_image(img, variables):
    """Redimensionne, convertit en niveaux de gris et seuille l'image source."""
    img_ht, img_wd = img.shape[0], img.shape[1]
    img = cv2.resize(img, (variables.resize_wd, variables.resize_ht))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Égalisation de l'histogramme de couleur (CLAHE) - cl1 n'est pas utilisé directement plus tard
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(3, 3))
    cl1 = clahe.apply(img_gray)

    # Seuil adaptatif gaussien
    img_thresh = cv2.adaptiveThreshold(
        img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10
    )

    # Ajout des éléments requis à l'objet variables
    variables.img_ht = img_ht
    variables.img_wd = img_wd
    variables.img_gray = img_gray
    variables.img_thresh = img_thresh
    variables.img = img
    return variables


def preprocess_hand_image(hand_path, hand_mask_path, variables):
    """Charge et pré-traite l'image de la main et son masque."""
    hand = cv2.imread(hand_path)
    hand_mask = cv2.imread(hand_mask_path, cv2.IMREAD_GRAYSCALE)

    top_left, bottom_right = get_extreme_coordinates(hand_mask)
    hand = hand[top_left[1] : bottom_right[1], top_left[0] : bottom_right[0]]
    hand_mask = hand_mask[top_left[1] : bottom_right[1], top_left[0] : bottom_right[0]]
    hand_mask_inv = 255 - hand_mask

    # Standardisation des masques de main
    hand_mask = hand_mask / 255
    hand_mask_inv = hand_mask_inv / 255

    # Rendre le fond de la main noir
    hand_bg_ind = np.where(hand_mask == 0)
    hand[hand_bg_ind] = [0, 0, 0]

    # Obtention des dimensions de l'image et de la main
    hand_ht, hand_wd = hand.shape[0], hand.shape[1]

    variables.hand_ht = hand_ht
    variables.hand_wd = hand_wd
    variables.hand = hand
    variables.hand_mask = hand_mask
    variables.hand_mask_inv = hand_mask_inv
    return variables


def get_extreme_coordinates(mask):
    """Trouve les coordonnées minimales et maximales des pixels blancs (255) dans un masque."""
    indices = np.where(mask == 255)
    # Extraire les coordonnées x et y des pixels.
    x = indices[1]
    y = indices[0]

    # Trouver les coordonnées x et y minimales et maximales.
    topleft = (np.min(x), np.min(y))
    bottomright = (np.max(x), np.max(y))

    return topleft, bottomright


def draw_hand_on_img(
    drawing,
    hand,
    drawing_coord_x,
    drawing_coord_y,
    hand_mask_inv,
    hand_ht,
    hand_wd,
    img_ht,
    img_wd,
):
    """Dessine (superpose) l'image de la main sur l'image 'drawing' aux coordonnées données."""
    remaining_ht = img_ht - drawing_coord_y
    remaining_wd = img_wd - drawing_coord_x
    
    # Déterminer la taille de la main à cropper pour éviter de dépasser les bords de l'image
    crop_hand_ht = min(remaining_ht, hand_ht)
    crop_hand_wd = min(remaining_wd, hand_wd)

    hand_cropped = hand[:crop_hand_ht, :crop_hand_wd]
    hand_mask_inv_cropped = hand_mask_inv[:crop_hand_ht, :crop_hand_wd]

    # Coordonnées pour l'insertion
    y_slice = slice(drawing_coord_y, drawing_coord_y + crop_hand_ht)
    x_slice = slice(drawing_coord_x, drawing_coord_x + crop_hand_wd)

    # Masquer la zone pour la main (mettre le fond à 0 en utilisant le masque inversé)
    for i in range(3): # Pour chaque canal de couleur (B, G, R)
        drawing[y_slice, x_slice][:, :, i] = (
            drawing[y_slice, x_slice][:, :, i] * hand_mask_inv_cropped
        )

    # Ajouter l'image de la main
    drawing[y_slice, x_slice] = (
        drawing[y_slice, x_slice]
        + hand_cropped
    )
    return drawing


def draw_masked_object(
    variables, object_mask=None, skip_rate=5, black_pixel_threshold=10
):
    """
    Implémente la logique de dessin en quadrillage.
    Sépare l'image en blocs, sélectionne le bloc le plus proche à dessiner
    et enregistre la trame.
    """
    # print("Skip Rate: ", skip_rate)
    
    # Si un masque d'objet est fourni, le seuil s'appliquera uniquement à cette zone
    img_thresh_copy = variables.img_thresh.copy()
    if object_mask is not None:
        object_mask_black_ind = np.where(object_mask == 0)
        img_thresh_copy[object_mask_black_ind] = 255

    selected_ind_val = None
    selected_ind = 0
    
    # Initialize animation data if JSON export is enabled
    if variables.export_json:
        variables.animation_data = {
            "drawing_sequence": [],
            "frames_written": []
        }
    
    # Calculer le nombre de coupes pour la grille
    n_cuts_vertical = int(math.ceil(variables.resize_ht / variables.split_len))
    n_cuts_horizontal = int(math.ceil(variables.resize_wd / variables.split_len))

    # Construire la grille de tuiles (même les tuiles de bord de taille inégale)
    grid_of_cuts = []
    for i in range(n_cuts_vertical):
        row_cuts = []
        for j in range(n_cuts_horizontal):
            y_start = i * variables.split_len
            y_end = min(y_start + variables.split_len, variables.resize_ht)
            x_start = j * variables.split_len
            x_end = min(x_start + variables.split_len, variables.resize_wd)
            tile = img_thresh_copy[y_start:y_end, x_start:x_end]
            row_cuts.append(tile)
        grid_of_cuts.append(row_cuts)
    
    # Note: grid_of_cuts is kept as nested lists (not converted to numpy array)
    # because tiles can have inconsistent sizes at image borders

    # Trouver les tuiles (tiles) contenant au moins un pixel noir
    cut_black_indices = []
    for i in range(n_cuts_vertical):
        for j in range(n_cuts_horizontal):
            if np.sum(grid_of_cuts[i][j] < black_pixel_threshold) > 0:
                cut_black_indices.append((i, j))
    
    cut_black_indices = np.array(cut_black_indices)


    counter = 0
    # Continue tant qu'il y a des tuiles à dessiner
    while len(cut_black_indices) > 0:
        if selected_ind >= len(cut_black_indices):
            selected_ind = 0 
            
        selected_ind_val = cut_black_indices[selected_ind].copy()
        
        # Récupérer la tuile à dessiner (peut être de taille variable)
        tile_to_draw = grid_of_cuts[selected_ind_val[0]][selected_ind_val[1]]
        tile_ht, tile_wd = tile_to_draw.shape # <-- On récupère la taille réelle
        
        # Calculer les coordonnées de la tuile sélectionnée EN UTILISANT LA TAILLE RÉELLE
        range_v_start = selected_ind_val[0] * variables.split_len
        range_v_end = range_v_start + tile_ht # MODIFIÉ pour utiliser la taille réelle de la tuile
        range_h_start = selected_ind_val[1] * variables.split_len
        range_h_end = range_h_start + tile_wd # MODIFIÉ pour utiliser la taille réelle de la tuile

        # Créer une image BGR à partir de la tuile en niveaux de gris
        temp_drawing = np.zeros((tile_ht, tile_wd, 3), dtype=np.uint8)
        temp_drawing[:, :, 0] = tile_to_draw
        temp_drawing[:, :, 1] = tile_to_draw
        temp_drawing[:, :, 2] = tile_to_draw
        
        # Appliquer la tuile au cadre de dessin - CECI EST LA LIGNE CORRIGÉE
        variables.drawn_frame[range_v_start:range_v_end, range_h_start:range_h_end] = temp_drawing

        # Coordonnées pour le centre de la main
        hand_coord_x = range_h_start + int(tile_wd / 2)
        hand_coord_y = range_v_start + int(tile_ht / 2)
        
        # Dessiner la main
        drawn_frame_with_hand = draw_hand_on_img(
            variables.drawn_frame.copy(),
            variables.hand.copy(),
            hand_coord_x,
            hand_coord_y,
            variables.hand_mask_inv.copy(),
            variables.hand_ht,
            variables.hand_wd,
            variables.resize_ht,
            variables.resize_wd,
        )

        # Supprimer l'index sélectionné
        cut_black_indices = np.delete(cut_black_indices, selected_ind, axis=0)

        # Sélectionner le nouvel index le plus proche
        if len(cut_black_indices) > 0:
            euc_arr = euc_dist(cut_black_indices, selected_ind_val)
            selected_ind = np.argmin(euc_arr)
        else:
            selected_ind = -1 

        counter += 1
        if counter % skip_rate == 0 or len(cut_black_indices) == 0:
            variables.video_object.write(drawn_frame_with_hand)
            
            # Capture animation data if JSON export is enabled
            if variables.export_json:
                frame_data = {
                    "frame_number": len(variables.animation_data["frames_written"]),
                    "tile_drawn": {
                        "grid_position": [int(selected_ind_val[0]), int(selected_ind_val[1])],
                        "pixel_coords": {
                            "x_start": int(range_h_start),
                            "x_end": int(range_h_end),
                            "y_start": int(range_v_start),
                            "y_end": int(range_v_end)
                        }
                    },
                    "hand_position": {
                        "x": int(hand_coord_x),
                        "y": int(hand_coord_y)
                    },
                    "tiles_remaining": int(len(cut_black_indices))
                }
                variables.animation_data["frames_written"].append(frame_data)

        if counter % 40 == 0 and len(cut_black_indices) > 0:
            print(f"Tuiles restantes: {len(cut_black_indices)}")

    # Après avoir dessiné toutes les lignes, superposer l'objet original en couleur
    if object_mask is not None:
        object_ind = np.where(object_mask == 255)
        variables.drawn_frame[object_ind] = variables.img[object_ind]
    else:
        variables.drawn_frame[:, :, :] = variables.img


def draw_whiteboard_animations(
    img, mask_path, hand_path, hand_mask_path, save_video_path, variables
):
    """Fonction principale pour orchestrer l'animation de dessin."""
    object_mask_exists = (mask_path is not None)

    # 1. Pré-traitement de l'image source et de la main
    variables = preprocess_image(img=img, variables=variables)
    variables = preprocess_hand_image(
        hand_path=hand_path, hand_mask_path=hand_mask_path, variables=variables
    )

    start_time = time.time()

    # 2. Définition de l'objet vidéo
    if platform == "android":
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    else:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v") 
        
    variables.video_object = cv2.VideoWriter(
        save_video_path,
        fourcc,
        variables.frame_rate,
        (variables.resize_wd, variables.resize_ht),
    )

    # 3. Création d'un cadre vide (fond blanc)
    variables.drawn_frame = np.zeros(variables.img.shape, np.uint8) + np.array(
        [255, 255, 255], np.uint8
    )

    # 4. Dessin de l'animation
    # Dessiner l'image entière sans masque
    draw_masked_object(
        variables=variables,
        skip_rate=variables.object_skip_rate,
    )


    # 5. Fin de la vidéo avec l'image originale en couleur
    for i in range(variables.frame_rate * variables.end_gray_img_duration_in_sec):
        variables.video_object.write(variables.img)

    end_time = time.time()
    print(f"Temps total d'exécution pour le dessin: {end_time - start_time:.2f} secondes")

    # 6. Fermeture de l'objet vidéo
    variables.video_object.release()


def export_animation_json(variables, json_path):
    """Exporte les données d'animation au format JSON."""
    if not variables.animation_data:
        print("⚠️ Aucune donnée d'animation à exporter.")
        return False
    
    try:
        # Convert numpy types to Python native types
        def convert_to_native(obj):
            """Convertit les types numpy en types Python natifs."""
            if isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64,
                               np.uint8, np.uint16, np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            else:
                return obj
        
        export_data = {
            "metadata": {
                "frame_rate": int(variables.frame_rate),
                "width": int(variables.resize_wd),
                "height": int(variables.resize_ht),
                "split_len": int(variables.split_len),
                "object_skip_rate": int(variables.object_skip_rate),
                "total_frames": len(variables.animation_data["frames_written"]),
                "hand_dimensions": {
                    "width": int(variables.hand_wd),
                    "height": int(variables.hand_ht)
                }
            },
            "animation": convert_to_native(variables.animation_data)
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Données d'animation exportées: {json_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export JSON: {e}")
        return False


def apply_entrance_animation(frame, layer_img, animation_config, progress):
    """
    Applique une animation d'entrée à une couche.
    
    Args:
        frame: Frame de base sur laquelle composer
        layer_img: Image de la couche à animer
        animation_config: Configuration de l'animation {"type": "fade_in", "duration": 1.0}
        progress: Progression de l'animation (0.0 à 1.0)
    
    Returns:
        Frame composée avec l'animation appliquée
    """
    if not animation_config or progress >= 1.0:
        return cv2.addWeighted(frame, 1, layer_img, 1, 0)
    
    anim_type = animation_config.get("type", "none")
    
    if anim_type == "fade_in":
        alpha = progress
        return cv2.addWeighted(frame, 1, layer_img, alpha, 0)
    
    elif anim_type == "slide_in_left":
        offset = int((1 - progress) * frame.shape[1])
        result = frame.copy()
        if offset < frame.shape[1]:
            shift_img = np.roll(layer_img, -offset, axis=1)
            result = cv2.addWeighted(result, 1, shift_img, 1, 0)
        return result
    
    elif anim_type == "slide_in_right":
        offset = int((1 - progress) * frame.shape[1])
        result = frame.copy()
        if offset < frame.shape[1]:
            shift_img = np.roll(layer_img, offset, axis=1)
            result = cv2.addWeighted(result, 1, shift_img, 1, 0)
        return result
    
    elif anim_type == "zoom_in":
        scale = 0.5 + (progress * 0.5)
        h, w = layer_img.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        if new_h > 0 and new_w > 0:
            resized = cv2.resize(layer_img, (new_w, new_h))
            result = frame.copy()
            y_offset = (h - new_h) // 2
            x_offset = (w - new_w) // 2
            if y_offset >= 0 and x_offset >= 0 and y_offset + new_h <= h and x_offset + new_w <= w:
                result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            return result
    
    return cv2.addWeighted(frame, 1, layer_img, 1, 0)


def apply_camera_transform(img, camera_config):
    """
    Applique une transformation de caméra (zoom et position focale).
    
    Args:
        img: Image à transformer
        camera_config: {"zoom": 1.5, "position": {"x": 0.5, "y": 0.5}}
    
    Returns:
        Image transformée
    """
    if not camera_config:
        return img
    
    zoom = camera_config.get("zoom", 1.0)
    position = camera_config.get("position", {"x": 0.5, "y": 0.5})
    
    h, w = img.shape[:2]
    
    # Calculate crop dimensions
    crop_h = int(h / zoom)
    crop_w = int(w / zoom)
    
    # Calculate focus point
    focus_x = int(w * position["x"])
    focus_y = int(h * position["y"])
    
    # Calculate crop boundaries
    x1 = max(0, focus_x - crop_w // 2)
    y1 = max(0, focus_y - crop_h // 2)
    x2 = min(w, x1 + crop_w)
    y2 = min(h, y1 + crop_h)
    
    # Adjust if crop exceeds boundaries
    if x2 - x1 < crop_w:
        x1 = max(0, x2 - crop_w)
    if y2 - y1 < crop_h:
        y1 = max(0, y2 - crop_h)
    
    # Crop and resize back to original size
    cropped = img[y1:y2, x1:x2]
    if cropped.size > 0:
        return cv2.resize(cropped, (w, h))
    return img


def apply_post_animation_effect(video_frames, animation_config, frame_rate):
    """
    Applique des effets d'animation post-dessin (zoom in/out).
    
    Args:
        video_frames: Liste des frames déjà générées
        animation_config: {"type": "zoom_in", "duration": 2.0, "start_zoom": 1.0, "end_zoom": 2.0, ...}
        frame_rate: FPS de la vidéo
    
    Returns:
        Liste de frames avec l'effet appliqué
    """
    if not animation_config or animation_config.get("type") == "none":
        return video_frames
    
    anim_type = animation_config.get("type")
    duration = animation_config.get("duration", 1.0)
    start_zoom = animation_config.get("start_zoom", 1.0)
    end_zoom = animation_config.get("end_zoom", 2.0)
    focus_pos = animation_config.get("focus_position", {"x": 0.5, "y": 0.5})
    
    num_frames = int(duration * frame_rate)
    if num_frames == 0 or len(video_frames) == 0:
        return video_frames
    
    # Get the last frame as the base
    base_frame = video_frames[-1].copy()
    result_frames = []
    
    for i in range(num_frames):
        progress = i / num_frames
        
        if anim_type == "zoom_in":
            current_zoom = start_zoom + (end_zoom - start_zoom) * progress
        elif anim_type == "zoom_out":
            current_zoom = start_zoom - (start_zoom - end_zoom) * progress
        else:
            current_zoom = 1.0
        
        # Apply zoom
        camera_config = {
            "zoom": current_zoom,
            "position": focus_pos
        }
        transformed = apply_camera_transform(base_frame, camera_config)
        result_frames.append(transformed)
    
    return result_frames


def process_layer_with_animation(layer_config, variables, base_frame, prev_layer_frame=None):
    """
    Traite une couche avec toutes ses propriétés et animations.
    
    Args:
        layer_config: Configuration de la couche
        variables: Variables globales
        base_frame: Frame de base (blanc)
        prev_layer_frame: Frame de la couche précédente pour le morphing
    
    Returns:
        Liste de frames pour cette couche
    """
    # Load layer image
    image_path = layer_config.get("image_path")
    if not image_path or not os.path.exists(image_path):
        print(f"⚠️ Image de couche introuvable: {image_path}")
        return []
    
    layer_img = cv2.imread(image_path)
    if layer_img is None:
        print(f"⚠️ Impossible de charger l'image: {image_path}")
        return []
    
    # Get layer properties
    position = layer_config.get("position", {"x": 0, "y": 0})
    scale = layer_config.get("scale", 1.0)
    opacity = layer_config.get("opacity", 1.0)
    skip_rate = layer_config.get("skip_rate", variables.object_skip_rate)
    mode = layer_config.get("mode", "draw")
    
    # Apply scale
    if scale != 1.0:
        new_w = int(layer_img.shape[1] * scale)
        new_h = int(layer_img.shape[0] * scale)
        if new_w > 0 and new_h > 0:
            layer_img = cv2.resize(layer_img, (new_w, new_h))
    
    # Resize to match canvas
    layer_img = cv2.resize(layer_img, (variables.resize_wd, variables.resize_ht))
    
    # Apply position offset (simplified - overlay at position)
    if position["x"] != 0 or position["y"] != 0:
        shifted = np.zeros_like(layer_img)
        h, w = layer_img.shape[:2]
        x_off = int(position["x"])
        y_off = int(position["y"])
        
        # Calculate valid region
        src_x1 = max(0, -x_off)
        src_y1 = max(0, -y_off)
        src_x2 = min(w, w - x_off) if x_off < 0 else min(w, w)
        src_y2 = min(h, h - y_off) if y_off < 0 else min(h, h)
        
        dst_x1 = max(0, x_off)
        dst_y1 = max(0, y_off)
        dst_x2 = min(w, dst_x1 + (src_x2 - src_x1))
        dst_y2 = min(h, dst_y1 + (src_y2 - src_y1))
        
        if dst_x2 > dst_x1 and dst_y2 > dst_y1:
            shifted[dst_y1:dst_y2, dst_x1:dst_x2] = layer_img[src_y1:src_y2, src_x1:src_x2]
        layer_img = shifted
    
    # Apply opacity
    if opacity < 1.0:
        layer_img = (layer_img * opacity).astype(np.uint8)
    
    # Process image for drawing
    layer_processed = preprocess_image(layer_img.copy(), 
                                       AllVariables(frame_rate=variables.frame_rate,
                                                   resize_wd=variables.resize_wd,
                                                   resize_ht=variables.resize_ht,
                                                   split_len=variables.split_len,
                                                   object_skip_rate=skip_rate,
                                                   bg_object_skip_rate=variables.bg_object_skip_rate,
                                                   end_gray_img_duration_in_sec=0))
    
    # Handle different modes
    if mode == "static":
        # No animation - just return the layer composited on base
        return [cv2.addWeighted(base_frame, 1, layer_img, 1, 0)]
    
    # For "draw" and "eraser" modes, create drawing animation
    frames = []
    
    # Choose hand or eraser image
    if mode == "eraser":
        # Load eraser image if available, else use hand
        eraser_path = os.path.join(images_path, 'eraser.png')
        if os.path.exists(eraser_path):
            drawing_tool = cv2.imread(eraser_path)
        else:
            drawing_tool = variables.hand
        drawing_tool_mask = variables.hand_mask
    else:
        drawing_tool = variables.hand
        drawing_tool_mask = variables.hand_mask
    
    # Simplified drawing animation - just create frames with progressive reveal
    # This is a placeholder - the full implementation would use the tile-based drawing
    num_frames = max(10, int(variables.frame_rate * 2))  # At least 2 seconds
    
    for i in range(num_frames):
        progress = (i + 1) / num_frames
        # Simple alpha blending based on progress
        alpha = min(1.0, progress * 1.2)
        frame = cv2.addWeighted(base_frame, 1, layer_img, alpha, 0)
        frames.append(frame)
    
    return frames


def draw_slides_with_layers(config_path, variables, save_video_path):
    """
    Dessine une animation complète avec système de slides et couches.
    
    Args:
        config_path: Chemin vers le fichier JSON de configuration
        variables: Variables globales
        save_video_path: Chemin de sauvegarde de la vidéo
    
    Returns:
        True si succès, False sinon
    """
    try:
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        slides = config.get("slides", [])
        transitions = config.get("transitions", [])
        
        if not slides:
            print("⚠️ Aucune slide trouvée dans la configuration.")
            return False
        
        print(f"📊 Traitement de {len(slides)} slide(s)...")
        
        # Setup video writer
        if platform == "android":
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        else:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        
        video_writer = cv2.VideoWriter(
            save_video_path,
            fourcc,
            variables.frame_rate,
            (variables.resize_wd, variables.resize_ht),
        )
        
        # Process each slide
        all_slide_frames = []
        
        for slide_idx, slide in enumerate(slides):
            print(f"\n🎬 Traitement de la slide {slide_idx}...")
            
            slide_duration = slide.get("duration", 5)
            layers = slide.get("layers", [])
            
            if not layers:
                # No layers - use legacy single image if provided
                print(f"⚠️ Slide {slide_idx} n'a pas de couches, passage...")
                continue
            
            # Sort layers by z_index
            sorted_layers = sorted(layers, key=lambda l: l.get("z_index", 0))
            
            # Create base white frame
            base_frame = np.zeros((variables.resize_ht, variables.resize_wd, 3), np.uint8)
            base_frame[:] = [255, 255, 255]
            
            slide_frames = []
            prev_layer_frame = None
            
            # Process each layer
            for layer_idx, layer in enumerate(sorted_layers):
                print(f"  📄 Traitement de la couche {layer_idx} (z_index={layer.get('z_index', 0)})...")
                
                # Check for entrance animation
                entrance_anim = layer.get("entrance_animation")
                
                # Process layer
                layer_frames = process_layer_with_animation(layer, variables, base_frame, prev_layer_frame)
                
                if not layer_frames:
                    continue
                
                # Apply entrance animation if configured
                if entrance_anim:
                    anim_duration = entrance_anim.get("duration", 0.5)
                    anim_frames = int(anim_duration * variables.frame_rate)
                    
                    entrance_frames = []
                    for i in range(anim_frames):
                        progress = (i + 1) / anim_frames
                        frame = apply_entrance_animation(base_frame, layer_frames[-1], entrance_anim, progress)
                        entrance_frames.append(frame)
                    
                    slide_frames.extend(entrance_frames)
                else:
                    slide_frames.extend(layer_frames)
                
                # Update base frame with this layer
                if layer_frames:
                    base_frame = layer_frames[-1].copy()
                    prev_layer_frame = base_frame.copy()
                
                # Apply camera transform if configured
                camera_config = layer.get("camera")
                if camera_config and slide_frames:
                    for i in range(len(slide_frames)):
                        slide_frames[i] = apply_camera_transform(slide_frames[i], camera_config)
                
                # Apply post-animation effect if configured
                animation_config = layer.get("animation")
                if animation_config:
                    print(f"    🎭 Application de l'animation post-dessin: {animation_config.get('type')}...")
                    post_frames = apply_post_animation_effect([base_frame], animation_config, variables.frame_rate)
                    slide_frames.extend(post_frames)
                    if post_frames:
                        base_frame = post_frames[-1].copy()
            
            # Hold final frame for remaining slide duration
            current_duration = len(slide_frames) / variables.frame_rate
            remaining_duration = max(0, slide_duration - current_duration)
            hold_frames = int(remaining_duration * variables.frame_rate)
            
            if hold_frames > 0 and slide_frames:
                for _ in range(hold_frames):
                    slide_frames.append(slide_frames[-1].copy())
            
            all_slide_frames.append(slide_frames)
        
        # Apply transitions between slides
        final_frames = []
        for slide_idx, slide_frames in enumerate(all_slide_frames):
            final_frames.extend(slide_frames)
            
            # Check for transition after this slide
            transition = next((t for t in transitions if t.get("after_slide") == slide_idx), None)
            if transition and slide_idx < len(all_slide_frames) - 1:
                # Simple fade transition
                trans_type = transition.get("type", "fade")
                trans_duration = transition.get("duration", 0.5)
                trans_frames = int(trans_duration * variables.frame_rate)
                
                last_frame = slide_frames[-1] if slide_frames else base_frame
                next_frames = all_slide_frames[slide_idx + 1]
                first_next_frame = next_frames[0] if next_frames else base_frame
                
                for i in range(trans_frames):
                    alpha = (i + 1) / trans_frames
                    trans_frame = cv2.addWeighted(last_frame, 1 - alpha, first_next_frame, alpha, 0)
                    final_frames.append(trans_frame)
        
        # Write all frames
        print(f"\n✍️ Écriture de {len(final_frames)} frames...")
        for frame in final_frames:
            video_writer.write(frame)
        
        video_writer.release()
        print(f"✅ Vidéo générée avec succès!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement des slides: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_nearest_res(given):
    """Trouve la résolution standard la plus proche pour une dimension donnée."""
    arr = np.array([360, 480, 640, 720, 1080, 1280, 1440, 1920, 2160, 2560, 3840, 4320, 7680])
    idx = (np.abs(arr - given)).argmin()
    return arr[idx]

class AllVariables:
    """Classe conteneur pour toutes les variables et paramètres du processus."""
    def __init__(
        self,
        frame_rate=None,
        resize_wd=None,
        resize_ht=None,
        split_len=None,
        object_skip_rate=None,
        bg_object_skip_rate=None,
        end_gray_img_duration_in_sec=None,
        export_json=False,
    ):
        self.frame_rate = frame_rate
        self.resize_wd = resize_wd
        self.resize_ht = resize_ht
        self.split_len = split_len
        self.object_skip_rate = object_skip_rate
        self.bg_object_skip_rate = bg_object_skip_rate
        self.end_gray_img_duration_in_sec = end_gray_img_duration_in_sec
        self.export_json = export_json
        
        # Variables qui seront ajoutées plus tard
        self.img_ht = None
        self.img_wd = None
        self.img_gray = None
        self.img_thresh = None
        self.img = None
        self.hand_ht = None
        self.hand_wd = None
        self.hand = None
        self.hand_mask = None
        self.hand_mask_inv = None
        self.video_object = None
        self.drawn_frame = None
        
        # Variables pour l'export JSON
        self.animation_data = None


def common_divisors(num1, num2):
    """Trouve tous les diviseurs communs de deux nombres et les renvoie triés."""
    common_divs = []
    min_num = min(num1, num2)
    
    for i in range(1, min_num + 1):
        if num1 % i == 0 and num2 % i == 0:
            common_divs.append(i)
    return common_divs


def ffmpeg_convert(source_vid, dest_vid, platform="linux"):
    """Convertit la vidéo brute (mp4v) en H.264 compatible avec PyAV."""
    ff_stat = False
    try:
        import av
        src_path = Path(source_vid)
        input_container = av.open(src_path, mode="r")
        output_container = av.open(dest_vid, mode="w")
        
        in_stream = input_container.streams.video[0]
        width = in_stream.codec_context.width
        height = in_stream.codec_context.height
        fps = in_stream.average_rate
        
        # set output params
        out_stream = output_container.add_stream("h264", rate=fps)
        out_stream.width = width
        out_stream.height = height
        out_stream.pix_fmt = "yuv420p"
        out_stream.options = {"crf": "20"}

        for frame in input_container.decode(video=0):
            packet = out_stream.encode(frame)
            if packet:
                output_container.mux(packet)
                
        packet = out_stream.encode()
        if packet:
            output_container.mux(packet)
            
        output_container.close()
        input_container.close()

        print(f"✅ Conversion FFmpeg réussie. Fichier: {dest_vid}")
        ff_stat = True
        
    except ImportError:
        print("⚠️ AVERTISSEMENT: Le module 'av' (PyAV) n'est pas installé. La conversion H.264 sera ignorée.")
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion FFmpeg: {e}")
        
    return ff_stat


def initiate_sketch_sync(image_path, split_len, frame_rate, object_skip_rate, bg_object_skip_rate, main_img_duration, callback, save_path=save_path, which_platform="linux", export_json=False):
    """Version synchrone de initiate_sketch pour l'exécution en ligne de commande (sans Kivy Clock)."""
    global platform
    platform = which_platform
    final_result = {"status": False, "message": "Initial load"}
    try:
        if not (os.path.exists(hand_path) and os.path.exists(hand_mask_path)):
            raise FileNotFoundError(f"Fichiers de main manquants. Attendu dans: {images_path}")
            
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
             raise ValueError(f"Impossible de lire l'image: {image_path}")
             
        mask_path = None 

        now = datetime.datetime.now()
        current_time = str(now.strftime("%H%M%S"))
        current_date = str(now.strftime("%Y%m%d"))
        
        video_save_name = f"vid_{current_date}_{current_time}.mp4" 
        save_video_path = os.path.join(save_path, video_save_name)
        ffmpeg_file_name = f"vid_{current_date}_{current_time}_h264.mp4"
        ffmpeg_video_path = os.path.join(save_path, ffmpeg_file_name)
        json_file_name = f"animation_{current_date}_{current_time}.json"
        json_export_path = os.path.join(save_path, json_file_name)
        os.makedirs(os.path.dirname(save_video_path), exist_ok=True)
        print(f"Chemin de sauvegarde brut: {save_video_path}")

        img_ht, img_wd = image_bgr.shape[0], image_bgr.shape[1]
        aspect_ratio = img_wd / img_ht
        img_ht = find_nearest_res(img_ht)
        new_aspect_wd = int(img_ht * aspect_ratio)
        img_wd = find_nearest_res(new_aspect_wd)
        print(f"Résolution cible: {img_wd}x{img_ht}")

        variables = AllVariables(
            frame_rate=frame_rate, resize_wd=img_wd, resize_ht=img_ht, split_len=split_len, 
            object_skip_rate=object_skip_rate, bg_object_skip_rate=bg_object_skip_rate, 
            end_gray_img_duration_in_sec=main_img_duration, export_json=export_json
        )

        draw_whiteboard_animations(
            image_bgr, mask_path, hand_path, hand_mask_path, save_video_path, variables
        )
        
        # Export JSON if requested
        if export_json:
            export_animation_json(variables, json_export_path)
        
        ff_stat = ffmpeg_convert(source_vid=save_video_path, dest_vid=ffmpeg_video_path, platform=platform)
        
        if ff_stat:
            final_result = {"status": True, "message": f"{ffmpeg_video_path}"}
            os.unlink(save_video_path)
            print(f"Vidéo brute supprimée: {save_video_path}")
        else:
            final_result = {"status": True, "message": f"{save_video_path}"} 
        
        # Add JSON path to result if exported
        if export_json:
            final_result["json_path"] = json_export_path

    except Exception as e:
        final_result = {"status": False, "message": f"Erreur fatale: {e}"}

    callback(final_result)


def get_split_lens(image_path):
    """ Obtient la résolution de l'image (redimensionnée) et les diviseurs communs (split_lens). """
    final_return = {"image_res": "None", "split_lens": []}
    try:
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
             raise ValueError(f"Impossible de lire l'image: {image_path}")
             
        img_ht, img_wd = image_bgr.shape[0], image_bgr.shape[1]
        aspect_ratio = img_wd / img_ht
        img_ht = find_nearest_res(img_ht)
        new_aspect_wd = int(img_ht * aspect_ratio)
        img_wd = find_nearest_res(new_aspect_wd)
        
        hcf_list = common_divisors(img_ht, img_wd)
        filename = os.path.basename(image_path)
        
        final_return["split_lens"] = hcf_list
        final_return["image_res"] = f"{filename}, résolution vidéo cible: {img_wd}x{img_ht}"
    except Exception as e:
        final_return["image_res"] = f"Erreur lors de la lecture de l'image. {e}"
        print(f"Erreur lors de l'obtention des split lens: {e}")
        
    return final_return

# --- Configuration CLI (Ligne de Commande) ---

DEFAULT_FRAME_RATE = 30
DEFAULT_SPLIT_LEN = 15
DEFAULT_OBJECT_SKIP_RATE = 8
DEFAULT_BG_OBJECT_SKIP_RATE = 20
DEFAULT_MAIN_IMG_DURATION = 3

def main():
    """Fonction principale pour gérer les arguments CLI et lancer l'animation."""
    parser = argparse.ArgumentParser(
        description="Crée une vidéo d'animation style tableau blanc à partir d'une image ou d'une configuration JSON avec couches. "
        "Utilisez aussi --get-split-lens [image_path] pour voir les valeurs 'split_len' recommandées."
    )
    
    parser.add_argument(
        'image_path', 
        type=str, 
        nargs='?', 
        default=None,
        help="Le chemin du fichier image à animer OU le chemin du fichier JSON de configuration pour le mode couches"
    )

    parser.add_argument(
        '--config', 
        type=str,
        help="Mode couches: Chemin vers un fichier JSON de configuration définissant les slides et couches"
    )

    parser.add_argument(
        '--split-len', 
        type=int, 
        default=DEFAULT_SPLIT_LEN,
        help=f"Taille de grille pour le dessin. Par défaut: {DEFAULT_SPLIT_LEN}. Utilisez des diviseurs de la résolution pour de meilleurs résultats."
    )
    parser.add_argument(
        '--frame-rate', 
        type=int, 
        default=DEFAULT_FRAME_RATE,
        help=f"Images par seconde (FPS). Par défaut: {DEFAULT_FRAME_RATE}."
    )
    parser.add_argument(
        '--skip-rate', 
        type=int, 
        default=DEFAULT_OBJECT_SKIP_RATE,
        help=f"Vitesse de dessin. Plus grand = plus rapide. Par défaut: {DEFAULT_OBJECT_SKIP_RATE}."
    )
    parser.add_argument(
        '--bg-skip-rate', 
        type=int, 
        default=DEFAULT_BG_OBJECT_SKIP_RATE,
        help=f"Taux de saut pour l'arrière-plan (non utilisé ici sans masques). Par défaut: {DEFAULT_BG_OBJECT_SKIP_RATE}."
    )
    parser.add_argument(
        '--duration', 
        type=int, 
        default=DEFAULT_MAIN_IMG_DURATION,
        help=f"Durée en secondes de l'image finale. Par défaut: {DEFAULT_MAIN_IMG_DURATION}."
    )
    
    parser.add_argument(
        '--export-json',
        action='store_true',
        help="Exporte les données d'animation au format JSON (séquence de dessin, positions de la main, etc.)."
    )
    
    parser.add_argument(
        '--get-split-lens', 
        action='store_true',
        help="Affiche les valeurs 'split_len' recommandées pour le chemin d'image fourni, puis quitte."
    )

    args = parser.parse_args()
    
    if not (os.path.exists(hand_path) and os.path.exists(hand_mask_path)):
        print("\n❌ ERREUR DE CONFIGURATION: Les images de la main (drawing-hand.png et hand-mask.png) sont introuvables.")
        sys.exit(1)

    # --- Mode de vérification des 'split-lens' ---
    if args.get_split_lens:
        path_to_check = args.image_path
        if not path_to_check:
            print("Erreur: Vous devez spécifier le chemin de l'image après --get-split-lens.")
            return

        if not os.path.exists(path_to_check):
             print(f"Erreur: Le chemin d'image spécifié est introuvable: {path_to_check}")
             return
             
        res_info = get_split_lens(path_to_check)
        print("\n" + "="*50)
        print("INFOS DE RÉSOLUTION ET VALEURS 'SPLIT_LEN' RECOMMANDÉES")
        print("="*50)
        print(res_info['image_res'])
        print(f"Valeurs 'split_len' suggérées (diviseurs communs de la résolution cible):")
        print(res_info['split_lens'])
        print("\nUtilisez l'une de ces valeurs avec l'argument --split-len.")
        print("="*50 + "\n")
        return

    # --- Mode couches avec JSON ---
    config_file = args.config or (args.image_path if args.image_path and args.image_path.endswith('.json') else None)
    
    if config_file:
        if not os.path.exists(config_file):
            print(f"❌ Erreur: Le fichier de configuration est introuvable: {config_file}")
            return
        
        print("\n" + "="*50)
        print("🎬 Lancement de l'animation Whiteboard - Mode Couches")
        print(f"Configuration: {config_file}")
        print(f"Paramètres: Split={args.split_len}, FPS={args.frame_rate}")
        print("="*50)
        
        # Load config to get resolution
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Try to get resolution from config or use defaults
            width = config.get("width", 1280)
            height = config.get("height", 720)
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture du fichier de configuration: {e}")
            width, height = 1280, 720
        
        now = datetime.datetime.now()
        current_time = str(now.strftime("%H%M%S"))
        current_date = str(now.strftime("%Y%m%d"))
        
        video_save_name = f"vid_layers_{current_date}_{current_time}.mp4"
        save_video_path = os.path.join(save_path, video_save_name)
        ffmpeg_file_name = f"vid_layers_{current_date}_{current_time}_h264.mp4"
        ffmpeg_video_path = os.path.join(save_path, ffmpeg_file_name)
        os.makedirs(os.path.dirname(save_video_path), exist_ok=True)
        
        variables = AllVariables(
            frame_rate=args.frame_rate,
            resize_wd=width,
            resize_ht=height,
            split_len=args.split_len,
            object_skip_rate=args.skip_rate,
            bg_object_skip_rate=args.bg_skip_rate,
            end_gray_img_duration_in_sec=args.duration,
            export_json=args.export_json
        )
        
        # Preprocess hand images
        variables = preprocess_hand_image(hand_path, hand_mask_path, variables)
        
        # Process slides with layers
        success = draw_slides_with_layers(config_file, variables, save_video_path)
        
        if success:
            ff_stat = ffmpeg_convert(source_vid=save_video_path, dest_vid=ffmpeg_video_path, platform=platform)
            
            if ff_stat:
                print(f"\n✅ SUCCÈS! Vidéo enregistrée sous: {ffmpeg_video_path}")
                os.unlink(save_video_path)
            else:
                print(f"\n✅ SUCCÈS! Vidéo enregistrée sous: {save_video_path}")
        else:
            print(f"\n❌ ÉCHEC de la génération vidéo.")
        
        return

    # --- Mode de génération vidéo classique (image unique) ---
    if not args.image_path:
        parser.print_help()
        print("\n❌ ERREUR: Le chemin de l'image ou du fichier de configuration est manquant.")
        return

    if not os.path.exists(args.image_path):
        print(f"❌ Erreur: Le chemin d'image est introuvable: {args.image_path}")
        return

    print("\n" + "="*50)
    print("🎬 Lancement de l'animation Whiteboard")
    print(f"Image source: {args.image_path}")
    print(f"Paramètres: Split={args.split_len}, FPS={args.frame_rate}, Skip={args.skip_rate}")
    print("="*50)

    def final_callback_cli(result):
        """Fonction de rappel appelée à la fin de la génération."""
        if result["status"]:
            print(f"\n✅ SUCCÈS! Vidéo enregistrée sous: {result['message']}")
            if "json_path" in result:
                print(f"✅ Données d'animation exportées: {result['json_path']}")
        else:
            print(f"\n❌ ÉCHEC de la génération vidéo. Message: {result['message']}")

    # Appel de la fonction synchrone pour la CLI
    initiate_sketch_sync(
        args.image_path,
        args.split_len,
        args.frame_rate,
        args.skip_rate,
        args.bg_skip_rate,
        args.duration,
        final_callback_cli,
        export_json=args.export_json
    )

if __name__ == '__main__':
    main()