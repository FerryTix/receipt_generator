import pygame
from time import sleep
from .receipt_printer import ReceiptPrinter
from pygame import camera

pygame.init()
camera.init()

clist = pygame.camera.list_cameras()
cam = pygame.camera.Camera(clist[0], (640, 480))
display = pygame.display.set_mode((640, 480), 0)
snapshot = pygame.surface.Surface((640, 480), 0, display)
cam.start()


while True:
    sleep(0.1)
    if cam.query_image():
        snapshot = cam.get_image(snapshot)
        cam.stop()
        break

pygame.image.save(snapshot, "image.jpg")

sleep(1)

ReceiptPrinter().print_stream(open('receipt.yaml').read())
