# INSTALLÉ DANS JETSON
# Path actuel : ~/Desktop/ultralytics/2_Automated_servo_control_no_display_v2.py
import cv2
import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
import tensorrt as trt
import time
import datetime
import serial
import logging
import signal
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("Received signal to terminate. Resetting servos and exiting...")
    if 'servo_controller' in globals():
        servo_controller.reset_servos_to_initial_smooth()
        servo_controller.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)

# TensorRT and CUDA setup functions
def load_engine(engine_path):
    TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
    with open(engine_path, 'rb') as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())

def allocate_buffers(engine):
    inputs = []
    outputs = []
    bindings = []
    stream = cuda.Stream()
    for binding in engine:
        size = trt.volume(engine.get_binding_shape(binding))
        dtype = trt.nptype(engine.get_binding_dtype(binding))
        host_mem = cuda.pagelocked_empty(size, dtype)
        device_mem = cuda.mem_alloc(host_mem.nbytes)
        bindings.append(int(device_mem))
        if engine.binding_is_input(binding):
            inputs.append({'host': host_mem, 'device': device_mem})
        else:
            outputs.append({'host': host_mem, 'device': device_mem})
    return inputs, outputs, bindings, stream

def do_inference(context, bindings, inputs, outputs, stream):
    cuda.memcpy_htod_async(inputs[0]['device'], inputs[0]['host'], stream)
    context.execute_async_v2(bindings=bindings, stream_handle=stream.handle)
    for output in outputs:
        cuda.memcpy_dtoh_async(output['host'], output['device'], stream)
    stream.synchronize()
    return [output['host'] for output in outputs]

# Image processing functions
def preprocess_image(image, input_shape):
    resized = cv2.resize(image, (input_shape[3], input_shape[2]))
    img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    img = img.transpose(2, 0, 1).astype(np.float32)
    img /= 255.0
    img = np.expand_dims(img, axis=0)
    return img

def process_output(output, orig_shape, conf_threshold=0.25, iou_threshold=0.45):
    output = output.reshape(1, 5, -1).transpose(0, 2, 1)
    boxes = output[0, :, :4]
    scores = output[0, :, 4]

    mask = scores > conf_threshold
    boxes = boxes[mask]
    scores = scores[mask]

    if len(boxes) == 0:
        return np.array([]), np.array([])

    boxes[:, 0] -= boxes[:, 2] / 2
    boxes[:, 1] -= boxes[:, 3] / 2
    boxes[:, 2] += boxes[:, 0]
    boxes[:, 3] += boxes[:, 1]

    scale_x, scale_y = orig_shape[1] / 640, orig_shape[0] / 640
    boxes[:, [0, 2]] *= scale_x
    boxes[:, [1, 3]] *= scale_y

    boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, orig_shape[1])
    boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, orig_shape[0])

    indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), conf_threshold, iou_threshold)

    if len(indices) == 0:
        return np.array([]), np.array([])

    boxes = boxes[indices]
    scores = scores[indices]

    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    largest_idx = np.argmax(areas)

    return boxes[largest_idx:largest_idx+1], scores[largest_idx:largest_idx+1]

# Servo control functions
class ServoController:
    def __init__(self, port='/dev/esp32s3serial', baudrate=115200):
        self.ser = serial.Serial(port, baudrate)
        self.current_positions = {'PAN': 129, 'TILT': 52}
        self.target_positions = {'PAN': 129, 'TILT': 52}
        self.reset_servos_to_initial_smooth()
        self.last_movement_time = time.time()
        self.movement_timeout = 0.25  # 250ms timeout for movement completion
        self.last_face_detection_time = time.time()
        self.start_time = time.time()
        self.initialization_period = 3.0  # 3 seconds initialization period

    def move_servo(self, servo, position):
        command = f"{servo}:{position}\n"
        self.ser.write(command.encode())
        self.current_positions[servo] = position
        self.target_positions[servo] = position
        self.last_movement_time = time.time()
        logger.info(f"Servo {servo} moving to position: {position}")

    def move_servo_smooth(self, servo, target_position, steps=10, delay=0.05):
        current_position = self.current_positions[servo]
        step_size = (target_position - current_position) / steps

        for _ in range(steps):
            current_position += step_size
            self.move_servo(servo, int(round(current_position)))
            time.sleep(delay)

        # Ensure we reach the exact target position
        self.move_servo(servo, target_position)

    def reset_servos_to_initial_smooth(self):
        self.move_servo_smooth('PAN', 129)
        self.move_servo_smooth('TILT', 52)
        logger.info("Servos reset to initial position smoothly")

    def adjust_servos(self, diff_x, diff_y):
        current_time = time.time()
        if current_time - self.start_time < self.initialization_period:
            # During initialization, use smaller increments
            pan_increment = int(diff_x / 40)
            tilt_increment = int(diff_y / 40)
        else:
            pan_increment = int(diff_x / 20)
            tilt_increment = int(diff_y / 20)

        new_pan = self.current_positions['PAN'] + pan_increment
        new_tilt = self.current_positions['TILT'] - tilt_increment

        new_pan = max(0, min(270, new_pan))
        new_tilt = max(30, min(76, new_tilt))

        if new_pan != self.target_positions['PAN'] or new_tilt != self.target_positions['TILT']:
            self.move_servo('PAN', new_pan)
            self.move_servo('TILT', new_tilt)
            return True
        return False

    def is_movement_complete(self):
        return time.time() - self.last_movement_time > self.movement_timeout

    def update_face_detection_time(self):
        self.last_face_detection_time = time.time()

    def check_face_timeout(self, timeout=10):
        if time.time() - self.last_face_detection_time > timeout:
            logger.info(f"No face detected for {timeout} seconds. Resetting servos.")
            self.reset_servos_to_initial_smooth()
            self.last_face_detection_time = time.time()

    def close(self):
        self.reset_servos_to_initial_smooth()
        self.ser.close()

# Utility classes and functions
class ExponentialMovingAverage:
    def __init__(self, alpha=0.9):
        self.alpha = alpha
        self.value = None

    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def process_detections(frame, box, confidence, averaged_box=None):
    height, width = frame.shape[:2]
    center_x, center_y = width // 2, height // 2

    if len(box) > 0:
        x1, y1, x2, y2 = map(int, box[0])
        logger.info(f"Raw Face detected: ({x1}, {y1}, {x2}, {y2}) - Confidence: {confidence[0]:.2f}")
    else:
        logger.info("No Faces Detected")

    if averaged_box is not None and len(averaged_box) > 0:
        x1, y1, x2, y2 = map(int, averaged_box)
        logger.info(f"Averaged Face: ({x1}, {y1}, {x2}, {y2})")

        cursor_x = (x1 + x2) // 2
        cursor_y = y2 - (y2 - y1) // 4
        diff_x = center_x - cursor_x
        diff_y = center_y - cursor_y
        return diff_x, diff_y
    else:
        logger.info("No Averaged Faces")

    return None, None

# Main function
def main():
    global servo_controller  # Make servo_controller global so it can be accessed in the signal handler

    gst_pipeline = (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
        "nvvidconv flip-method=2 ! "
        "video/x-raw, format=BGRx ! "
        "videoconvert ! "
        "appsink"
    )

    engine = load_engine('yolov8n_Face_FP16.trt')
    context = engine.create_execution_context()
    input_shape = tuple(engine.get_binding_shape(0))
    inputs, outputs, bindings, stream = allocate_buffers(engine)

    servo_controller = ServoController()

    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    start_time = time.time()
    frame_count = 0
    servo_instruction_count = 0
    last_servo_instruction_time = time.time()

    movement_threshold = 30
    cooldown_period = 0.25

    ema_x1, ema_y1, ema_x2, ema_y2 = [ExponentialMovingAverage() for _ in range(4)]
    ema_diff_x, ema_diff_y = ExponentialMovingAverage(), ExponentialMovingAverage()

    face_detection_count = 0
    face_detection_threshold = 5

    if not cap.isOpened():
        logger.error("Error: Could not open video capture.")
    else:
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Frame capture failed, stopping.")
                    break

                frame_count += 1
                img = preprocess_image(frame, input_shape)
                np.copyto(inputs[0]['host'], img.ravel())

                outputs_data = do_inference(context, bindings, inputs, outputs, stream)

                box, confidence = process_output(outputs_data[-1], frame.shape)

                if len(box) > 0:
                    face_detection_count += 1
                    servo_controller.update_face_detection_time()
                    x1, y1, x2, y2 = box[0]
                    averaged_box = [
                        ema_x1.update(x1),
                        ema_y1.update(y1),
                        ema_x2.update(x2),
                        ema_y2.update(y2)
                    ]
                else:
                    face_detection_count = 0
                    averaged_box = None
                    servo_controller.check_face_timeout()

                diff_x, diff_y = process_detections(frame, box, confidence, averaged_box)

                current_time = time.time()
                if diff_x is not None and diff_y is not None and face_detection_count >= face_detection_threshold:
                    avg_diff_x = ema_diff_x.update(diff_x)
                    avg_diff_y = ema_diff_y.update(diff_y)

                    logger.info(f"Face position difference: X: {avg_diff_x:.2f}, Y: {avg_diff_y:.2f}")

                    if (abs(avg_diff_x) > movement_threshold or abs(avg_diff_y) > movement_threshold) and \
                    (current_time - last_servo_instruction_time) >= cooldown_period and \
                    servo_controller.is_movement_complete():
                        logger.info("Attempting servo adjustment")
                        if servo_controller.adjust_servos(avg_diff_x, avg_diff_y):
                            servo_instruction_count += 1
                            last_servo_instruction_time = current_time
                            logger.info(f"Servo instruction sent. Total instructions: {servo_instruction_count}")
                        else:
                            logger.info("No servo adjustment needed")
                    elif not servo_controller.is_movement_complete():
                        logger.info("Waiting for previous servo movement to complete")
                    elif (current_time - last_servo_instruction_time) < cooldown_period:
                        logger.info("In cooldown period")
                    else:
                        logger.info("Face movement below threshold")

                elapsed_time = current_time - start_time
                if elapsed_time > 0:
                    fps = frame_count / elapsed_time
                    servo_instructions_per_second = servo_instruction_count / elapsed_time
                    logger.info(f"FPS: {fps:.2f}, Servo Instructions/s: {servo_instructions_per_second:.2f}")

                time.sleep(0.01)  # Adjust as needed to control loop speed

        finally:
            cap.release()
            servo_controller.close()

            for input in inputs:
                input['device'].free()
            for output in outputs:
                output['device'].free()

    logger.info("Script completed.")

if __name__ == '__main__':
    main()