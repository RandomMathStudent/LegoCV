# LegoCV Architecture Specification

## Overview

LegoCV converts a photograph of a person's face into the most accurate LEGO minifigure by combining:

- Geometric facial measurements
- Semantic facial attributes
- A feature engineering pipeline
- A ranking model over LEGO parts

Core philosophy:

> Use pretrained models for perception, and custom ML for LEGO-specific reasoning.

## High-Level Pipeline

```text
                    Input Image
                         |
                         v
                Face Detection & Crop
                         |
            +------------+------------+
            |                         |
            v                         v
      MediaPipe                 Vision Language Model
            |                         |
     Facial Geometry          Semantic Attributes
            |                         |
            +------------+------------+
                         |
                         v
                 Feature Engineering
                         |
                         v
                LEGO Part Matcher
                         |
                         v
                  Ranked Candidates
                         |
                         v
               LEGO Avatar Generator
```

## Stage 1 - Image Acquisition

### Input

- JPG
- PNG
- Webcam frame

### Requirements

- Single frontal face preferred
- Image resolution >= 512x512
- RGB image

### Tasks

- Load image
- Resize while preserving aspect ratio
- Normalize color space
- Detect face
- Crop with padding
- Reject if confidence is below threshold

### Output

```python
FaceImage
```

## Stage 2 - Face Detection

### Recommended Libraries

- OpenCV
- InsightFace detector
- RetinaFace

### Responsibilities

- Detect face bounding box
- Estimate confidence
- Detect multiple faces
- Select primary face

### Output

```python
BoundingBox
FaceCrop
DetectionConfidence
```

## Stage 3 - MediaPipe Geometry Extraction

### Library

- MediaPipe Face Mesh

### Raw Output

- 468 facial landmarks
- Landmark components: x, y, z

### Feature Groups

#### Face Shape

Compute:

- Face width
- Face height
- Jaw width
- Forehead width
- Chin angle

Infer:

- Round
- Square
- Oval
- Heart
- Diamond
- Long

#### Eye Features

Extract:

- Eye width
- Eye height
- Eye spacing
- Eye openness
- Eye symmetry

#### Eyebrows

Measure:

- Thickness
- Distance to eye
- Curvature
- Length

#### Nose

Measure:

- Length
- Width
- Bridge angle
- Nose tip position

#### Mouth

Measure:

- Smile angle
- Lip width
- Lip fullness
- Mouth openness

#### Jaw

Measure:

- Jaw width
- Jaw angle
- Chin prominence

#### Head Pose

Estimate:

- Yaw
- Pitch
- Roll

### Geometry Output Example

```json
{
  "face_width": 0.72,
  "face_height": 1.02,
  "jaw_angle": 118,
  "eye_spacing": 0.19,
  "smile": 0.81,
  "head_pitch": 4
}
```

## Stage 4 - Vision Language Model

### Purpose

Generate semantic descriptors that are difficult or impossible to infer reliably from geometry alone.

### Recommended Models

- Qwen2.5-VL
- Florence-2
- Molmo
- GPT-4.1 (optional cloud)

### Prompt Contract

- Return JSON only
- Describe visible facial attributes suitable for matching LEGO minifigure parts

### Semantic Fields

- Hair: color, length, style, fringe, volume
- Facial hair: beard, mustache, goatee, sideburns
- Eyebrows: thickness, shape, color
- Eyes: color
- Glasses: type, frame color
- Expression: smile, neutral, frown, open mouth
- Accessories: hat, headphones, piercings
- Skin tone
- Estimated age
- Gender presentation

### Output Example

```json
{
  "hair": {
    "colour": "black",
    "length": "long",
    "style": "curly",
    "fringe": "none"
  },
  "glasses": {
    "present": true,
    "shape": "round"
  },
  "facial_hair": "light stubble",
  "expression": "smile",
  "skin_tone": "medium"
}
```

## Stage 5 - Feature Engineering

### Purpose

Merge geometry and semantics into one structured feature vector.

### Example Unified Feature Object

```python
{
  "face_shape": "oval",
  "eye_spacing": 0.18,
  "jaw_width": 0.74,
  "hair_colour": "black",
  "hair_style": "curly",
  "hair_length": "long",
  "glasses": "round",
  "smile": 0.83,
  "beard": "none"
}
```

### Encoding

- Continuous features normalized to 0-1
- Categorical features one-hot encoded

Example hair colors:

- Black
- Brown
- Blonde
- Red
- Grey
- White

Example hair styles:

- Straight
- Curly
- Wavy
- Afro
- Buzz
- Ponytail
- Braids

### Output

- Single feature vector
- Typical dimension: approximately 100-300

## Stage 6 - LEGO Database

Each LEGO asset is represented as a structured object.

### Hair Piece

```json
{
  "part_id": "92081",
  "colour": "black",
  "style": "curly",
  "length": "long",
  "gender": "neutral"
}
```

### Face Print

```json
{
  "part_id": "3626cp1234",
  "eyebrows": "thick",
  "expression": "smile",
  "beard": "none",
  "glasses": false
}
```

### Accessory

```json
{
  "part_id": "30162",
  "type": "round glasses",
  "colour": "black"
}
```

## Stage 7 - LEGO Part Matching Model

This is the custom ML component.

### Input

- Feature vector

### Output

- Score for every LEGO part candidate

Example scores:

- Hair part 92081 -> 0.94
- Face print 3626cp1234 -> 0.88
- Accessory round glasses -> 0.98

### Model Evolution Path

- Version 1: weighted scoring rules
- Version 2: gradient boosted trees
- Version 3: neural ranking model
- Version 4: learning-to-rank (LambdaMART, RankNet, ListNet)

## Scoring Strategy

Category weights (example):

- Hair: 40%
- Face print: 30%
- Expression: 10%
- Accessories: 10%
- Geometry: 10%

Overall score example:

```text
0.40 * Hair
+0.30 * Face
+0.10 * Expression
+0.10 * Glasses
+0.10 * Geometry
=0.92
```

## Stage 8 - Ranking

Instead of returning one result, return top-k candidates per category (for example, top 10).

Example hair ranking:

```text
1  92081  0.95
2  87994  0.90
3  3901   0.82
```

Apply similarly for:

- Face
- Glasses
- Hat
- Accessory

## Stage 9 - Avatar Generation

Assemble selected parts in order:

```text
Hair -> Head -> Torso -> Legs -> Accessories -> Render
```

## Suggested Project Structure

```text
legocv/
  models/
    mediapipe.py
    vlm.py
    matcher.py

  features/
    geometry.py
    semantics.py
    engineering.py

  database/
    lego_parts.json
    hair.json
    faces.json
    accessories.json

  ranking/
    scorer.py
    ranker.py

  render/
    renderer.py

  api/
    predict.py

  notebooks/

  tests/
```

## Future Extensions

- Fine-tune the VLM for LEGO-specific attribute extraction.
- Replace rule-based matching with a learned ranking model trained on user preferences.
- Add confidence estimates and explainability (for example: selected this hair because it matches long, curly, black hair).
- Incorporate body pose and clothing to recommend torso and leg pieces.
- Support multi-view images for more accurate hair and face analysis.
- Learn user-specific preferences over time using feedback.
