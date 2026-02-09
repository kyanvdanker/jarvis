"""A wearable raspberry pi zero w interface for Jarvis,
allowing voice recording and a connection to the main Jarvis brain
for processing and response generation. This is meant to be a lightweight
client that can be used on a small device, and will communicate with the main Jarvis brain over the internet.
it also has bmp180 for weather sensing and a mpu 6050
for motion sensing. The main purpose of this is to allow Jarvis to have a presence on the go, and to be able to interact with the user in a more natural way.
This runs only a small part and the main responses will be asked to the Main server aka the part that is not in wearable.
So it cant import anything from the main server aka the brain, memory, rocket simulation, and ollama client. It can only import from the local files in the wearable folder.
"""
