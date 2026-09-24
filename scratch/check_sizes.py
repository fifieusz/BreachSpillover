import os

# Let's inspect the first 10 frames of Clickingsound.mp3 in detail
with open("frontend/static/sounds/Clickingsound.mp3", "rb") as f:
    data = f.read()

# Let's check the size of Clickingsound vs Errorsound vs Exportbuttonsound
for fn in ["Clickingsound.mp3", "Errorsound.mp3", "Exportbuttonsound.mp3", "Searchingsound.mp3"]:
    fp = f"frontend/static/sounds/{fn}"
    print(f"{fn}: {os.path.getsize(fp)} bytes")
