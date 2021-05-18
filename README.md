[![GitHub issues](https://img.shields.io/github/issues/stautonico/blackhat-simulator?style=for-the-badge)](https://github.com/stautonico/blackhat-simulator/issues)
[![GitHub license](https://img.shields.io/github/license/stautonico/blackhat-simulator?style=for-the-badge)](https://github.com/stautonico/blackhat-simulator/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/stautonico/blackhat-simulator?style=for-the-badge)](https://github.com/stautonico/blackhat-simulator/stargazers)
![GitHub all releases](https://img.shields.io/github/downloads/stautonico/blackhat-simulator/total?style=for-the-badge)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/stautonico/blackhat-simulator?style=for-the-badge)

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/github_username/repo_name">
    <img src="https://via.placeholder.com/80" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Blackhat Simulator</h3>

  <p align="center">
    A Realistic hacking/penetration testing simulator/game
    <br />
    <a href="https://blackhat.tautonico.tech/docs/client">View Docs</a>
    ·
    <a href="https://github.com/stautonico/blackhat-simulator/issues/new?assignees=&labels=bug&template=bug_report.md&title=">Report Bug</a>
    ·
    <a href="https://github.com/stautonico/blackhat-simulator/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=">Request Feature</a>
    ·
    <a href="https://discord.gg/N7rktfNDgh">Join the discord</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->

## About The Project

<!--[![Product Name Screen Shot][product-screenshot]](https://example.com)-->

This game was inspired by the games [Grey Hack](https://store.steampowered.com/app/605230/Grey_Hack/)
, [Hacknet](https://store.steampowered.com/app/365450/Hacknet/),
and [NITE Team 4](https://store.steampowered.com/app/544390/NITE_Team_4__Military_Hacking_Division/) on steam. I
originally started this project in C++ because I wanted an easy way for the user to build and compile their own
binaries, then run them within the game without creating a programming language from scratch. This was accomplished by
compiling without standard libraries and using custom replacements that interact with the game instance instead of the
actual machine they're running on. However, due to my lack of knowledge of C++ (and probably many other reasons), I hit
a dead-end and put the project on pause for a while. I decided to re-start the project in python (without some features
I originally wanted) because I am much more knowledgeable when it comes to python. Note that this software is still in
very early stages, and many parts are subject to change.
<br />

**Note**: Some of the games "implementations" are only loosely based on their real world counterpart for one or more of
these reasons:

1. I was too lazy / will come back to it later
2. Since this is intended to be a simulator type game, some of these items might ruin the experience/won't be fun in a
   video game
3. My knowledge of the given topic isn't sufficient to create an accurate "implementation" of the item.

### Built With

* [Python3+](https://www.python.org/)
* [PyGame (Not yet)](https://www.pygame.org/)
* [SQLite(3)](https://www.sqlite.org/index.html)
* [My Big Brain](https://blackhat.tautonico.tech/errors/404.html?ref=github)

<!-- GETTING STARTED -->

## Getting Started

This program was only tested on Linux (arch specifically), but hypothetically, it should work on Windows (🤞)

### Prerequisites

Python must be installed. All dependencies are listed in [`requirements.txt`](requirements.txt)

### Installation

1. Clone the repo
   ```shell
   git clone https://github.com/stautonico/blackhat-simulator
   ```
2. Install dependencies
   ```shell
   pip install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->

## Usage

**To start the client:**

1. Make sure you followed all steps in <a href="#installation">#Installation</a>
2. ```cd client```
3. ```python3 main.py```

<br>

**To run the tests:**
1. Make sure you have all requirements installed: `pip install -r requirements.txt` 
2. `cd client`
3. `python -m unittest blackhat/tests/test_binaries.py`

All "documentation" is generated through the use of docstrings (google format) and `pdoc3`. **To generate
documentation:**

```shell
pdoc --html --output-dir docs -c show_source_code=True -c show_type_annotations=True client.blackhat
```

If you have an issue with overwriting, you can add the `--force` tag, which will automatically overwrite any old files.



<!-- ROAD MAP --->

## Road Map

**These are some features I have in mind (sorted by priority)**

### Close 🔍

- [ ] Increase "coreutils" functionality (most bins only have basic functionality, they should be more accurate to the
  real world)
- [ ] Manpages (None have manuals/instructions)

- [ ] Tests (As of now, any code, working or not working, gets pushed to main (that's not good lol))

- [ ] System logging (Real linux systems log stuff like auth attempts, network connections, etc)

### Far 🔭

- [ ] Multiplayer (This may be unlikely due to the fact that the "game" has many vulnerabilities that may allow the
  players' system to be compromised in a multiplayer scenario, but this may change in the future.)

- [ ] PyGame based UI (instead of terminal based game) (This is likely to occur, but isn't my top priority.)

- [ ] Story (As of now, this project is closer to being a game framework then being an actual game. After the project's
  functionality becomes more saturated, a single player "story" mode is likely to come to fruition.)

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any
contributions you make are **greatly appreciated**.

1. **READ [CONTRIBUTING.md](CONTRIBUTING.md)**
2. Fork the Project
3. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
4. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the Branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

<!-- LICENSE -->

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

<!-- ACKNOWLEDGEMENTS -->

## Acknowledgements

* [Robin Selmer (website error page)](https://codepen.io/robinselmer/pen/vJjbOZ?css-preprocessor=none)
* [kirb](https://github.com/kirb)
  / [theos](https://github.com/theos/theos) ([PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md))
