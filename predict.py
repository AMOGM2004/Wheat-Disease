# import tensorflow as tf
# import numpy as np
# from tensorflow.keras.preprocessing import image

# IMG_SIZE = 224
# model = tf.keras.models.load_model("wheat_model.h5")
# img_path = r"C:\Users\Bindu\Downloads\Wheat_Disease_Project\dataset\validation\LeafBlight\LeafBlight_4.jpg"
# img = image.load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))
# img_array = image.img_to_array(img)
# img_array = np.expand_dims(img_array, axis=0)
# img_array = img_array / 255.0
# prediction = model.predict(img_array)
# class_index = np.argmax(prediction)
# confidence = np.max(prediction)
# class_names = ["Healthy", "BlackPoint", "LeafBlight", "WheatBlast", "FusariumFootRot"]
# print("Predicted Disease:", class_names[class_index])
# print("Confidence:", confidence)


import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import sqlite3

IMG_SIZE = 224
model = tf.keras.models.load_model("wheat_model.h5")
class_names = ["Healthy", "BlackPoint", "LeafBlight", "WheatBlast", "FusariumFootRot"]

def predict_disease(img_path, farmer_name="Unknown", latitude=18.5204, longitude=73.8567):
    img = image.load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    prediction = model.predict(img_array)
    class_index = np.argmax(prediction)
    confidence = np.max(prediction)
    disease = class_names[class_index]

    # Save to database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO disease_reports (farmer_name, disease_name, latitude, longitude, image_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (farmer_name, disease, latitude, longitude, img_path))
    conn.commit()
    conn.close()

    return disease, confidence