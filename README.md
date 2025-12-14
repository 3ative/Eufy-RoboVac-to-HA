# Eufy RoboVac to HA

## Updates:
🥳 **Major Optimization Update - December 2025**
- Also, See here [Vacuum battery properties are deprecated](https://developers.home-assistant.io/blog/2025/07/02/vacuum-battery-properties-deprecated/) for why.
  
**What's New:**
- ✅ **78% reduction in database writes** (from ~26,000/day to ~5,760/day)
- ✅ **Fixes Home Assistant watchdog timeout reboots**
- ✅ **Modernized for Home Assistant 2025.5+ compatibility**
- ✅ **Smart caching prevents "unavailable" flickers**
- ✅ **Separate battery and charging sensors (future-proof for HA 2025.8+)**

**Technical Changes:**
- Added shared connection manager with intelligent rate limiting
- Vacuum updates: 30s (was 5s)
- Battery sensor: 60s (was 10s)
- Smart caching maintains availability during brief disconnects
- Modernized to StateVacuumEntity with VacuumActivity enum
- Removed deprecated platform.py

**Performance:**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Database writes/day | ~26,000 | ~5,760 | **78% reduction** |
| Watchdog reboots | Frequent | **None** | ✅ Fixed |

---
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

<div align="center">

### 💖 Support This Project

Found this useful? Want to say thanks and fuel future creations?

**Your support keeps the creativity flowing!** 🍺✨

<table>
  <tr>
    <td align="center">
      <a href="https://www.buymeacoffee.com/3ative">
        <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white" alt="Buy Me A Coffee"/>
        <br/>
        <b>☕ Buy me a Coffee</b>
      </a>
    </td>
    <td align="center">
      <a href="https://www.patreon.com/3ative">
        <img src="https://img.shields.io/badge/Patreon-Become%20a%20Patron-red.svg?style=for-the-badge&logo=patreon&logoColor=white" alt="Patreon"/>
        <br/>
        <b>💖 Join on Patreon</b>
      </a>
    </td>
  </tr>
</table>

**Every contribution helps bring more awesome projects to life!** 🚀

</div>

---

