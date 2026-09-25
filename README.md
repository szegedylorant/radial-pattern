# radial-pattern
Radial pattern generator plugin for KiCad 10

## Usage

* Select a shape, e.g. a hole for a potentiometer

* Click on plugin icon ![star shaped icon with dot inside](icon.png)

* Set parameters and generate pattern

## Example

![radial pattern of decreasing length lines with increasing density](example.png)

## Installation

* Clone repo to 

```
~/.local/share/kicad/10.0/plugins/
```

* Restart KiCad

* Icon for plugin should appear in pcbnew

## Issues

* Groupping does not remain after deselecting generated objects
    - Workaround: after plugin finishes, Right Click --> Groupping --> Group Items
