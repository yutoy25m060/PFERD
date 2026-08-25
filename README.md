# The Poses for Equine Research Dataset (PFERD)

This repository is the official PyTorch codes of: 

The Poses for Equine Research Dataset (PFERD) \
Ci Li, Ylva Mellbin, Johanna Krogager, Senya Polikovsky, Martin Holmberg, Nima Ghorbani, Michael J. Black, Hedvig Kjellström, Silvia Zuffi and Elin Hernlund

In Scientific Data 2024

[Paper](https://www.nature.com/articles/s41597-024-03312-1)

![front](front.jpg)

PFERD, a dense motion capture dataset of horses of diverse conformation and poses with rich 3D horse articulated motion data. This repository provides codes to visualize the data and evaluate the data.

## Repository Guide

This is the original upstream PFERD codebase (visualization/evaluation demos below). This fork
additionally includes a custom data-processing pipeline under `scripts/` — see
[README_my_pipeline.md](README_my_pipeline.md) for its documentation (Japanese). AI coding
assistants working in this repo should also read [CLAUDE.md](CLAUDE.md).

## Installation

The codes are tested with Python 3.8, PyTorch 1.8.2, Aitviewer v1.9.0. The environment is managed
with [uv](https://docs.astral.sh/uv/); dependencies are pinned in `pyproject.toml` / `uv.lock`.

``` bash
git clone --recurse-submodules https://github.com/Celiali/PFERD.git
cd PFERD
uv sync
```

`uv sync` downloads Python 3.8 (per `.python-version`) if needed and installs everything into
`.venv`, including torch/torchvision/torchaudio from the PyTorch LTS 1.8 (cu111) index. Run
scripts with `uv run python <script>`, or activate `.venv` directly.

**Not included:** `ezc3d` (for loading `.c3d` mocap files) — the PyPI package requires Python
>= 3.10, which conflicts with the Python 3.8 pin required by `torch==1.8.2`. It's only needed for
the optional `--VISUAL_MOCAP` overlay in [Load_Visualization.py](Load_Visualization.py), not for
the core `scripts/` pipeline. If you need it, install it in a separate conda environment
(`conda install -c conda-forge ezc3d=1.4.9`) or build it from source with CMake + a C++ compiler.

For the original upstream evaluation scripts ([Eval_iou.py](Eval_iou.py),
[Eval_3Ddistance.py](Eval_3Ddistance.py), [Projection.py](Projection.py)), you'll additionally need
`human_body_prior`, `body_visualizer`, and `psbody.mesh`/`psbody.smpl` — see
[SOMA](https://github.com/nghorbani/soma) for `psbody` installation, which typically requires a
Linux build environment and is not covered by the uv setup above.

After installing, run `uv run python scripts/check_setup.py` to verify required packages,
model/dataset paths, and device configuration before running any demo or pipeline script.


## Access to the hSMAL Model
The hSMAL model is available at this [link](https://sites.google.com/view/cv4horses/cv4horses).
Download the hSMAL model and place it under `./hSMALdata` folder.

## Access to the PFERD Dataset 
The dataset for PFERD is available at [https://doi.org/10.7910/DVN/2EXONE](https://doi.org/10.7910/DVN/2EXONE).
Download the PFERD dataset, place it under `./dataset` folder and follow the directory structure of the data as below. We also provide a demo folder in the link.
```
|-- dataset
    |-- DEMO
    |-- [Subject ID]
        |-- C3D_DATA
            |--  [Trial Name].c3d
        |-- CAM_DATA
            |-- Camera_Miqus_Video_[Camera ID].npz
        |-- FBX_DATA
            |-- [Trial Name].fbx
        |-- KP2D_DATA
            |-- [Trial Name]
                |-- [Trial Name]_[Camera Code]_2Dkp.npz
        |-- MODEL_DATA
            |-- [Trial Name]_hsmal.npz
            |-- [Subject ID]_stagei.npz
        |-- SEGMENT_DATA
            |-- [Trial Name]_[Camera Code]_seg.mp4
        |-- VIDEO_DATA
            |-- [Trial Name]
                |-- [Trial Name]_[Camera Code].avi
```

To download video data for each Subject ID, follow these steps: 1. Download all parts of the split files and place them in a single folder; 2.Merge and extract the data with the following commands; 3. Place the data according to the above data structure.
```angular2html
cd /path/to/downloaded/split_files/Subject ID  # Replace Subject ID with the actual ID
cat VIDEO_DATA.tar.gz.part-* > VIDEO_DATA_recovered.tar.gz
tar -xzf VIDEO_DATA_recovered.tar.gz
```

Data structure
```angular2html
Camera_Miqus_Video_[Camera ID].npz :
'R': rotation, 'T': translation, 'K': instrinsic parameters, 'D': Distortion parameters
```
```angular2html
[Trial Name]_[Camera Code]_2Dkp.npz :
'kp2d': 2D keypoints, 'mocap3d': 3D mocap, 'labels': names of the keypoints, 'videoFps': video framerate, 'videoFrameNum': video frame number
```

```angular2html
[Trial Name]_hsmal.npz :
'betas': beta parameters,  'poses': pose parameters, 'trans': translation parameters, 'missing_frame': frames where no model information 
```

```angular2html
[Subject ID]_stagei.npz :
'betas': beta parameters,  'marker_latent': the latent representation of the optimized marker positions, 'labels': names of the markers, 'flag': markers visible during Stage I optimization   
```

## Run demo code

- Update file path in ```CONFIG.py```.


- Loading c3d files and the hSMAL model with the captured parameters to visualize the mocap data and the fitted results.
  
```angular2html
python Load_Visualization.py --ID 1 --mocapname '20201128_ID_1_0007' --VISUAL_MOCAP
```

- Projecting the reconstructed model in image planes with provided camera information.
```angular2html
python Projection.py --ID 1 --mocapname '20201128_ID_1_0007' --cameraID '20715' --VISUAL --VISUAL_MOCAP
```  

- Quantitative evaluation using the mocap data and silhouette subsets.
```angular2html
python Eval_3Ddistance.py --ID 1 --mocapname '20201128_ID_1_0007' --VISUAL
python Eval_iou.py --ID 1 --mocapname '20201128_ID_1_0007' --VISUAL
```

## License
License for the hSMAL Model: Please read carefully the [terms and conditions](https://sites.google.com/view/cv4horses/license?authuser=0) before you download and/or use the data.

License for the PFERD Dataset: Please read carefully the [terms and conditions](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/2EXONE&version=1.0&selectTab=termsTab) before you download and/or use the data.

License for this code: This code is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
- **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- **NonCommercial** — You may not use the material for commercial purposes.
- **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

Full license text available at: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode

## Acknowledgements
The project was supported by a career grant from SLU No. 57122058, received by Elin Hernlund. 
Silvia Zuffi was in part supported by the European Commission’s NextGeneration EU Programme, PNRR grant PE0000013 Future Artificial Intelligence Research—FAIR CUP B53C22003630006. 
The authors sincerely thank Tove Kjellmark for her assistance during the data collection and all horses and owners for their collaboration in the data collection experiments. Thank you to Zala Zgank for helping with the labeling of motion capture data.

Thank Peter Kulits for providing interface for [Aitviewer](https://github.com/eth-ait/aitviewer). 
This work is based on [moshpp](https://github.com/nghorbani/moshpp).
Thanks for the authors for their efforts. 

## Citation
If you find this code useful for your research or use the dataset, please consider citing the following paper:
```
@article{li2024poses,
  title={The Poses for Equine Research Dataset (PFERD)},
  author={Li, Ci and Mellbin, Ylva and Krogager, Johanna and Polikovsky, Senya and Holmberg, Martin and Ghorbani, Nima and Black, Michael J and Kjellstr{\"o}m, Hedvig and Zuffi, Silvia and Hernlund, Elin},
  journal={Scientific Data},
  volume={11},
  number={1},
  pages={497},
  year={2024},
  publisher={Nature Publishing Group UK London}
}
```