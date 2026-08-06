# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

PFERD is the official code release accompanying the paper "The Poses for Equine Research Dataset (PFERD)" (Scientific Data, 2024). It is a small research codebase — not a library or service — for loading, visualizing, and evaluating a horse motion-capture dataset against the hSMAL (horse SMAL) parametric body model. There is no test suite, linter, CI, or build system; everything is a standalone script run directly with `python <script>.py`.

## Setup

Target environment: Python 3.7, PyTorch 1.8.2, tested on Ubuntu 18, using conda.

```bash
git clone --recurse-submodules https://github.com/Celiali/PFERD.git
conda create -n PFERD python=3.7
conda activate PFERD
pip install torch==1.8.2 torchvision==0.9.2 torchaudio==0.8.2 --extra-index-url https://download.pytorch.org/whl/lts/1.8/cu111
pip install opencv-python==4.7.0.72
pip install chumpy
pip install smplx[all]          # visualization
pip install aitviewer==1.9.0    # visualization
conda install -c conda-forge ezc3d=1.4.9   # loading .c3d mocap files
conda install -c conda-forge loguru        # evaluation
conda install -c anaconda scikit-learn=1.0.2   # evaluation
pip install git+https://github.com/nghorbani/human_body_prior.git@SOMA
pip install git+https://github.com/nghorbani/body_visualizer.git
```

`psbody.smpl` and `psbody.mesh` (needed only by `Eval_3Ddistance.py`) are installed per the [SOMA](https://github.com/nghorbani/soma) instructions, not via pip/conda here.

**Submodule**: `moshpp/` is a git submodule (`nghorbani/moshpp`) providing mocap-reading (`MocapSession`) and mesh-fitting/marker utilities (`TransformedCoeffs`, `TransformedLms`, `bodymodel_loader`). It must be checked out with `git submodule update --init` — in a fresh checkout it is otherwise empty.

**External data (gitignored, downloaded separately, not part of this repo)**:
- `hSMALdata/` — hSMAL model files: `my_smpl_0000_horse_new_skeleton_horse.pkl`/`.npz` and the pose-prior `.pkl`. Available from the [hSMAL model page](https://sites.google.com/view/cv4horses/cv4horses).
- `dataset/` — the PFERD mocap dataset, one folder per Subject ID containing `C3D_DATA`, `CAM_DATA`, `FBX_DATA`, `KP2D_DATA`, `MODEL_DATA`, `SEGMENT_DATA`, `VIDEO_DATA` subfolders (see README.md for the exact layout and per-file field descriptions). Available via [Harvard Dataverse](https://doi.org/10.7910/DVN/2EXONE); a `DEMO` subject is provided for quick testing.

All filesystem paths and the compute device are centralized in `CONFIG.py` (`ModelPATH`, `ModelPriorPATH`, `ModelNPZPATH`, `DatasetPATH`, `DEVICE`) — update these before running anything against your own data location.

## Commands

There is no build, lint, or test tooling. All four entry points are standalone scripts with argparse CLIs:

```bash
python Load_Visualization.py --ID 1 --mocapname '20201128_ID_1_0007' --VISUAL_MOCAP
python Projection.py --ID 1 --mocapname '20201128_ID_1_0007' --cameraID '20715' --VISUAL --VISUAL_MOCAP
python Eval_3Ddistance.py --ID 1 --mocapname '20201128_ID_1_0007' --VISUAL
python Eval_iou.py --ID 1 --mocapname '20201128_ID_1_0007' --VISUAL
```

`--ID` selects the subject, `--mocapname` selects the trial, `--VISUAL`/`--VISUAL_MOCAP` toggle interactive display (aitviewer / matplotlib / psbody MeshViewer depending on the script). All scripts require a GPU-backed `DEVICE` and windowing support for `--VISUAL*` flags.

## Architecture

**`CONFIG.py`** is the single source of truth for paths and device, and every script starts with `import CONFIG` before any `moshpp`/`utils` import — this has the side effect of appending `moshpp/src` to `sys.path`, which is required for the submodule's imports to resolve.

**Four independent entry-point scripts**, all following the same load-mocap → load-hSMAL-fit-results → (load camera/model) → compute pattern:

- **`Load_Visualization.py`** — loads a trial's `{mocapname}_hsmal.npz` fit results plus optional `.c3d` mocap markers, wraps the fit as an aitviewer `SMPLSequence` via `utils.smal.SMALLayer`, and renders it interactively.
- **`Projection.py`** — reprojects the fitted 3D hSMAL mesh into each camera's image plane using `human_body_prior`'s `BodyModel` (loaded from the `.npz` model variant) and `utils.project`, overlaying observed 2D mocap markers across the 10 camera views for visual comparison.
- **`Eval_3Ddistance.py`** — quantitative marker-distance eval: uses moshpp's `TransformedCoeffs`/`TransformedLms` plus the Stage-I marker-latent representation (`{Subject}_stagei.npz`) to reconstruct simulated marker positions and compares them to observed C3D markers (per-marker Euclidean distance, NaN for occluded/missing markers or frames).
- **`Eval_iou.py`** — quantitative silhouette eval: renders the fitted mesh's silhouette per frame/camera via `utils.render.Renderer` and computes IoU against ground-truth segmentation videos (`SEGMENT_DATA/*_seg.mp4`).

**Two body-model code paths coexist by design and are not interchangeable**: aitviewer's `SMPLLayer`/`SMPLSequence` (wrapped in `utils/smal.py` as `SMALLayer`/`SMAL`/`HSMAL`, used only by `Load_Visualization.py` for the interactive viewer) vs. `human_body_prior`'s `BodyModel` (used by `Projection.py` and `Eval_iou.py` for headless rendering/eval). Both ultimately wrap the same hSMAL model, but one loads the `.pkl` and the other the `.npz` variant.

**`utils/`** holds shared helpers:
- `readfile.py` — `read_mocap` (wraps moshpp's `MocapSession`), `read_results` (loads `*_hsmal.npz` and broadcasts per-subject betas across frames), `read_cams` (loads per-camera `R`/`T`/`K`/`D` from `CAM_DATA/*.npz`), `get_imgs` (frame-indexed video reading, with optional undistortion).
- `project.py` — `get_cams_renderers` (builds a `Renderer` per camera from intrinsics), `reproject_masks` (applies camera rotation/translation and lens distortion to mesh vertices, then renders a silhouette/mask/composited image per camera), `reproject_keypoints` (OpenCV `projectPoints` of 3D markers into 2D per camera).
- `render.py` — `Renderer`, a pyrender/trimesh offscreen-rendering wrapper (adapted from smplify-x/CLIFF); requires `PYOPENGL_PLATFORM=egl`.
- `smal.py` — `SMAL`/`HSMAL` (subclass `smplx.SMPL` with horse-specific joint counts and shape-space dimensions) and `SMALLayer` (aitviewer `SMPLLayer` adapted to an HSMAL body model).

**Data/ID conventions**: `--ID` indexes `dataset/DEMO/ID_{ID}/...`; `--mocapname` (e.g. `20201128_ID_1_0007`) identifies a capture trial and keys into that subject's `C3D_DATA`, `MODEL_DATA`, `VIDEO_DATA`, `SEGMENT_DATA`, `CAM_DATA` subfolders. Mocap is captured at 240Hz while video is lower-fps, so frame alignment across the two is done via `interval = mocap.frame_rate / video_fps` and indexing mocap/results arrays at `frame * interval`.
