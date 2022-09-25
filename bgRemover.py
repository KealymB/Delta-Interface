import numpy as np
import cv2
from glob import glob
from tqdm import tqdm
import tensorflow as tf
from tensorflow.keras.utils import CustomObjectScope
from metrics import dice_loss, dice_coef, iou

def removeBG(size):
    """ Global parameters """
    H = size[0]
    W = size[1]

    """ Seeding """
    np.random.seed(42)
    tf.random.set_seed(42)

    """ Loading model: DeepLabV3+ """
    with CustomObjectScope({'iou': iou, 'dice_coef': dice_coef, 'dice_loss': dice_loss}):
        model = tf.keras.models.load_model("model.h5")

    """ Read the image """
    image = cv2.imread("snapShot.bmp", cv2.IMREAD_COLOR)
    h, w, _ = image.shape
    x = cv2.resize(image, (W, H))
    x = x/255.0
    x = x.astype(np.float32)
    x = np.expand_dims(x, axis=0)

    """ Prediction """
    y = model.predict(x)[0]
    y = cv2.resize(y, (w, h))
    y = np.expand_dims(y, axis=-1)
    y = y > 0.5

    photo_mask = y
    background_mask = np.abs(1-y)

    masked_photo = image * photo_mask
    background_mask = np.concatenate([background_mask, background_mask, background_mask], axis=-1)
    background_mask = background_mask * [255, 255, 255]
    final_photo = masked_photo + background_mask

    final_photo = final_photo.astype(np.uint8)

    cv2.imwrite("snapShot.bmp", final_photo)