# Project James Facial Gestures

This directory contains the original facial-state artwork for the three
1.83-inch LCD face: two portrait eye displays and one landscape mouth
display.

## Directory layout

```text
facial-gestures/
  manifest.yaml
  source/
    core-states/             High-resolution runtime-state concepts
    presentation-modifiers/ High-resolution behavioural modifiers
  export/                    Reserved for firmware-ready per-panel assets
```

The files under `source/` are master concept sprites produced with the
built-in OpenAI image-generation tool. They are intentionally retained at
high resolution because the exact installed LCD revision has not yet been
physically verified.

Do not load the source images directly in firmware. Each source currently
presents the complete three-screen face and must be reviewed, separated into
left-eye, right-eye and mouth frames, cleaned, and rasterized for the confirmed
panel revision.

## Display export targets

The Waveshare 1.83-inch module has two documented revisions:

| Revision | Controller | Portrait eye target | Landscape mouth target |
|---|---|---:|---:|
| Rev1 | NV3030B | 240 x 280 | 280 x 240 |
| Rev2 | ST7789P | 240 x 284 | 284 x 240 |

Confirm the marking on the rear of every physical module before populating
`export/`. Rev1 and Rev2 use different controller initialization and pixel
heights.

## Visual language

- background: pure black;
- primary expression colour: cyan (`#19D9FF` target);
- warning accent: amber/yellow;
- error accent: red/orange;
- restrained micro-expression rather than constant exaggerated motion;
- stillness is a valid part of the visual vocabulary;
- no copied character graphics, logos or text;
- all active pixels must remain inside a safe margin after export.

## Animation guidance

Static sources are key poses, not complete animations. Firmware animation
should use short transitions and lightweight procedural effects:

- `idle`: rare blink and very small gaze drift;
- `attentive`: quick orientation change, then settle;
- `listening`: immediate local acknowledgement and a slow pulse;
- `heard`: brief acknowledgement pose before `thinking`;
- `thinking`: subtle loop, never frantic;
- `acting`: restrained directional activity ticks;
- `speaking`: mouth amplitude frames derived from the speaking key pose;
- `success`: brief reaction, then gradual return to idle;
- `uncertain`: hesitant pause before clarification;
- `warning`: sharper transition with amber accent;
- `error`: clear failure pose without comic distress;
- `offline`: dim, still, unmistakably unavailable;
- `sleep`: dim closed-eye pose with minimal or no movement;
- `boot`: ordered progress animation until the runtime is ready.

Presentation modifiers should alter motion frequency, intensity or pose
selection without replacing the active runtime state or implying genuine
emotion.

## Source requirements

The state inventory is derived from:

- `docs/Design-Specification.md`, sections 24.2 and 26;
- `docs/Personality-Distillation.md`, sections 8 and 14;
- `docs/Firmware-Software-Roadmap.md`, WP01 and WP02.

The generation prompt family requested a hardware-independent three-panel
sprite, crisp cyan pixel/line graphics on black, generous safe margins,
restrained original micro-expressions, and clean downsampling to the documented
Waveshare resolutions. State-specific expression details are recorded in
`manifest.yaml`.
