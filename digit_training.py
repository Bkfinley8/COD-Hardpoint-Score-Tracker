import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import cv2

def preprocess_fn(img):
    if img is None:
        print("[ERROR] Got None image input")
        return img  # or handle error appropriately

    img = (img * 255).astype(np.uint8)

    if img.ndim == 3:
        img = np.squeeze(img, axis=-1)  # (28,28,1) -> (28,28)

    img = make_square(img)  # your padding function
    img = cv2.resize(img, (28, 28), interpolation=cv2.INTER_AREA)

    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=-1)



def make_square(image):
    if image.ndim == 3 and image.shape[-1] == 1:
        image = image.squeeze(axis=-1)  # convert (H, W, 1) → (H, W)

    h, w = image.shape[:2]
    size = max(h, w)
    square = np.ones((size, size), dtype=np.uint8) * 255  # white background

    y_offset = (size - h) // 2
    x_offset = (size - w) // 2
    square[y_offset:y_offset + h, x_offset:x_offset + w] = image

    return square




datagen = ImageDataGenerator(
    preprocessing_function=preprocess_fn,
    validation_split=0.2
)



train = datagen.flow_from_directory(
    'digit_dataset',
    target_size=(28, 28),  # still needed for directory parsing
    color_mode='grayscale',
    class_mode='categorical',
    subset='training'
)

val = datagen.flow_from_directory(
    'digit_dataset',
    target_size=(28, 28),
    color_mode='grayscale',
    class_mode='categorical',
    subset='validation'
)

model = models.Sequential([
    layers.Input(shape=(28, 28, 1)),  # or (56, 56, 1) if you're using larger inputs
    layers.Conv2D(32, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(10, activation='softmax')  # 10 output classes (digits 0–9)
])


model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(train, validation_data=val, epochs=10)
model.save('digit_model.h5')
