<img src="https://github.com/user-attachments/assets/fd345865-775c-432d-b9d3-be7e6e7ace0b" width="300" />


## Update

- Added Line ESP
  - You can now toggle on or off Line ESP for both entities or npc players.
  - Color is by default red.

<img src="https://github.com/user-attachments/assets/efdf3bfb-e963-404a-a286-cab9c18b31b3" width="300" />

# Morrowind-ESP-Overlay
This Python script creates an overlay for *The Elder Scrolls III: Morrowind* that displays additional information about in-game entities. Features include showing entity names, health bars, and health values in real-time. The overlay is rendered using PyQt5, while memory reading is done via `pymem` to fetch game data.

- I had issues getting this to work, find out way at this [UC Forum](https://www.unknowncheats.me/forum/other-single-player-games/679656-python-morrowind-npc-esp.html)

## Features

- **ESP Overlay**: Displays the names and health of in-game entities.
- **Health Bars**: Shows a graphical health bar for each entity.
- **Health Values**: Displays the current health of each entity in numerical form.
- **Customization**: Toggle visibility of entity names, health bars, and health values via a simple GUI.
  
## Requirements

- Python 3.6+
- [pymem](https://github.com/souhailk/pymem)
- [PyQt5](https://riverbankcomputing.com/software/pyqt/intro)
- [tkinter](https://wiki.python.org/moin/TkInter)


```
pip install pymem pyqt5 tkinter
```

## How It Works

- **Memory Reading**: The script uses `pymem` to read the game's memory, extracting data such as entity positions, health, and names.
- **Overlay Rendering**: The overlay is created using PyQt5, rendering entity data over the game window.
- **GUI Controls**: Tkinter is used for a simple graphical interface to toggle the visibility of entity names, health bars, and health values.

If the view matrix doesn't work properly for you, you may need to find your own. You can use the software given to find that, use the information in the UC forum to find that.
