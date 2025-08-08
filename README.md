# Eufy RoboVac to HA

## Updates:
🥳 I've done another full code rewrite. Tested on Home Assistant 2025.8.0 - See changes and new files above.
- Also, See here [Vacuum battery properties are deprecated](https://developers.home-assistant.io/blog/2025/07/02/vacuum-battery-properties-deprecated/) for why.
- Added file: binary_sensor.py = Charging Status
- Added file: sensor.py = New Battery Percentage
- Rewrote other files to include the new sensors BACK as Atrributes to ``vacuum.xxx`` entity
#
- #### You now have to register your device with the new App on your phone.
- #### From there "share" it with the old App (In BlueStacks), as shown in the tutorial.
#
Download for [BlueStacks here](https://www.bluestacks.com/)

Grab the files using the "**Code**" Button and select "**Download ZIP**"

![code_button](https://user-images.githubusercontent.com/51385971/135938718-13bb186b-e18d-47f7-8e08-269cc2a904be.jpg)

Config Entry:
``` yaml
eufy_vacuum:
  devices:
    - name: WizzVac1
      address: 
      access_token: 
      id: 
      type: T2118
```


# Watch the full tutorial here: https://youtu.be/dx5RuNgU8CY 

---
### 🤝 Found this useful, want to say 'Thanks' and support my efforts. CHEERS🍺
| Buy me a Coffee | PATREON |
|-----------------|---------|
| [![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow.svg?style=flat-square&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/3ative) | [![Patreon](https://img.shields.io/badge/Patreon-support-red.svg?style=flat-square&logo=patreon)](https://www.patreon.com/3ative) |
---
