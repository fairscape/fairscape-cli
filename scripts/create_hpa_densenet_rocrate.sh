#!/bin/bash

# =============================================================================
# HPA DenseNet RO-Crate Builder Script
# =============================================================================
# This script creates an RO-Crate for the Human Protein Atlas (HPA) DenseNet
# model based on the Kaggle competition "Human Protein Atlas Image Classification"
#
# References:
# - Paper: https://doi.org/10.1038/s41592-019-0658-6
# - Base Model: https://huggingface.co/timm/densenet121.tv_in1k
# - ImageNet Dataset: https://huggingface.co/datasets/ILSVRC/imagenet-1k
# - HPA Data: https://www.proteinatlas.org/about/download
# =============================================================================

set -e  # Exit on error

# Configuration
ROCRATE_PATH="./hpa-densenet-rocrate"
TODAY=$(date +%Y-%m-%d)

echo "=== Creating HPA DenseNet RO-Crate ==="
echo "Output directory: $ROCRATE_PATH"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Create the RO-Crate
# -----------------------------------------------------------------------------
echo "Step 1: Creating RO-Crate..."

fairscape-cli rocrate create "$ROCRATE_PATH" \
  --name "HPA DenseNet Image Classification" \
  --organization-name "Human Protein Atlas" \
  --project-name "HPA Image Classification Competition" \
  --description "RO-Crate containing the HPA DenseNet model for subcellular protein localization classification. This model was developed as part of the Human Protein Atlas Image Classification competition on Kaggle, which aimed to develop deep learning solutions for multi-label classification of protein subcellular localization patterns in confocal microscopy images. The winning solution achieved a macro F1 score of 0.593, outperforming previous methods by ~20%." \
  --keywords "deep learning" \
  --keywords "image classification" \
  --keywords "protein localization" \
  --keywords "Human Protein Atlas" \
  --keywords "DenseNet" \
  --keywords "subcellular localization" \
  --keywords "confocal microscopy" \
  --keywords "multi-label classification" \
  --keywords "Kaggle competition" \
  --author "Wei Ouyang, Casper F. Winsnes, Martin Hjelmare, Anthony J. Cesnik, Emma Lundberg et al." \
  --version "1.0" \
  --license "https://creativecommons.org/licenses/by/4.0/" \
  --date-published "$TODAY" \
  --associated-publication "https://doi.org/10.1038/s41592-019-0658-6"

echo "RO-Crate created."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Register the Base Model - DenseNet121 from HuggingFace
# -----------------------------------------------------------------------------
echo "Step 2: Registering base model (DenseNet121 from timm)..."

# Use the HuggingFace registration command to fetch metadata automatically
DENSENET_GUID=$(fairscape-cli rocrate register hf "timm/densenet121.tv_in1k" "$ROCRATE_PATH" \
  --description "DenseNet-121 model pretrained on ImageNet-1k. DenseNet (Densely Connected Convolutional Networks) connects each layer to every other layer in a feed-forward fashion. For each layer, the feature-maps of all preceding layers are used as inputs, and its own feature-maps are used as inputs into all subsequent layers. This architecture alleviates the vanishing-gradient problem, strengthens feature propagation, encourages feature reuse, and substantially reduces the number of parameters. This specific variant is from the torchvision implementation trained on ImageNet-1k with 1000 classes." \
  --model-type "Convolutional Neural Network" \
  --framework "PyTorch" \
  --model-format "safetensors" \
  --intended-use-case "Image classification, feature extraction, transfer learning for biological image analysis" \
  --usage-information "Can be used as a pretrained backbone for downstream tasks including protein subcellular localization classification")

echo "Base model registered with GUID: $DENSENET_GUID"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Register ImageNet-1k Dataset
# -----------------------------------------------------------------------------
echo "Step 3: Registering ImageNet-1k dataset..."

IMAGENET_GUID=$(fairscape-cli rocrate register dataset "$ROCRATE_PATH" \
  --name "ImageNet-1k (ILSVRC2012)" \
  --author "Olga Russakovsky, Jia Deng, Hao Su, Jonathan Krause, Sanjeev Satheesh, Sean Ma, Zhiheng Huang, Andrej Karpathy, Aditya Khosla, Michael Bernstein, Alexander C. Berg, Li Fei-Fei" \
  --version "1.0.0" \
  --description "ImageNet Large Scale Visual Recognition Challenge 2012 (ILSVRC2012) dataset, commonly known as ImageNet-1k. Contains 1,281,167 training images, 50,000 validation images, and 100,000 test images across 1,000 object categories. The dataset is widely used for training and benchmarking image classification models. Images are variable size with typical dimensions around 469x387 pixels. Each image is labeled with one of 1000 synset categories derived from WordNet. This dataset was used to pretrain the DenseNet121 model that serves as the base for the HPA classification model." \
  --keywords "ImageNet" \
  --keywords "ILSVRC" \
  --keywords "image classification" \
  --keywords "benchmark dataset" \
  --keywords "computer vision" \
  --keywords "deep learning" \
  --keywords "object recognition" \
  --data-format "JPEG images" \
  --date-published "2012-01-01" \
  --content-url "https://huggingface.co/datasets/ILSVRC/imagenet-1k" \
  --url "https://image-net.org/" \
  --associated-publication "https://doi.org/10.1007/s11263-015-0816-y" \
  --additional-documentation "https://www.image-net.org/challenges/LSVRC/2012/")

echo "ImageNet-1k dataset registered with GUID: $IMAGENET_GUID"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Register Computation - DenseNet Training on ImageNet
# -----------------------------------------------------------------------------
echo "Step 4: Registering DenseNet training computation..."

TRAINING_COMP_GUID=$(fairscape-cli rocrate register computation "$ROCRATE_PATH" \
  --name "DenseNet121 Training on ImageNet-1k" \
  --run-by "Ross Wightman (timm library)" \
  --date-created "2019-01-01" \
  --description "Training computation for DenseNet-121 model on ImageNet-1k dataset. The model was trained using the torchvision implementation with standard ImageNet training procedures including data augmentation (random resized crop, horizontal flip), SGD optimizer with momentum, and learning rate scheduling. Training was performed on GPU hardware. The resulting model achieves competitive top-1 and top-5 accuracy on the ImageNet validation set." \
  --keywords "model training" \
  --keywords "deep learning" \
  --keywords "ImageNet" \
  --keywords "DenseNet" \
  --keywords "PyTorch" \
  --used-dataset "$IMAGENET_GUID" \
  --generated "$DENSENET_GUID" \
  --additional-documentation "https://github.com/huggingface/pytorch-image-models")

echo "Training computation registered with GUID: $TRAINING_COMP_GUID"
echo ""

# -----------------------------------------------------------------------------
# Step 5: Register HPA Dataset
# -----------------------------------------------------------------------------
echo "Step 5: Registering Human Protein Atlas dataset..."

HPA_DATASET_GUID=$(fairscape-cli rocrate register dataset "$ROCRATE_PATH" \
  --name "Human Protein Atlas Subcellular Localization Images" \
  --author "Human Protein Atlas Consortium, Emma Lundberg, Mathias Uhlen" \
  --version "18.0" \
  --description "Immunofluorescence microscopy image dataset from the Human Protein Atlas Cell Atlas project. The dataset contains confocal microscopy images mapping subcellular protein localization across 27 human cell lines. Each image has four channels: protein of interest (green), microtubules (red), nucleus (blue), and endoplasmic reticulum (yellow). Images are annotated with 28 subcellular localization classes including nucleoplasm, cytosol, plasma membrane, mitochondria, Golgi apparatus, and others. The competition dataset consisted of 42,774 images (31,072 training, 11,702 test) with multi-label annotations (1-6 labels per image). The dataset exhibits high class imbalance, with nucleoplasm being the most common label (12,885 images) and rods and rings being the rarest (11 images). Image dimensions are typically 2048x2048 or 3072x3072 pixels at 16-bit depth with 0.08 um pixel size." \
  --keywords "Human Protein Atlas" \
  --keywords "subcellular localization" \
  --keywords "immunofluorescence" \
  --keywords "confocal microscopy" \
  --keywords "protein imaging" \
  --keywords "cell biology" \
  --keywords "multi-label classification" \
  --keywords "proteomics" \
  --data-format "TIFF/PNG images" \
  --date-published "2018-10-03" \
  --content-url "https://www.kaggle.com/c/human-protein-atlas-image-classification/data" \
  --url "https://www.proteinatlas.org/about/download" \
  --associated-publication "https://doi.org/10.1126/science.aal3321" \
  --additional-documentation "https://www.proteinatlas.org/humanproteome/subcellular")

echo "HPA dataset registered with GUID: $HPA_DATASET_GUID"
echo ""

# -----------------------------------------------------------------------------
# Step 6: Register Computation - HPA DenseNet Fine-tuning
# -----------------------------------------------------------------------------
echo "Step 6: Registering HPA DenseNet training computation..."

HPA_TRAINING_GUID=$(fairscape-cli rocrate register computation "$ROCRATE_PATH" \
  --name "HPA DenseNet Classification Model Training" \
  --run-by "Shubin Dai (Team bestfitting, Kaggle Competition Winner)" \
  --date-created "2019-01-10" \
  --description "Training computation for the winning HPA Image Classification model. The solution used DenseNet-121 as the backbone architecture, pretrained on ImageNet-1k, and fine-tuned on the HPA subcellular localization dataset. Key techniques employed: (1) Combined loss function with Lovasz loss term for multi-label classification, (2) Cyclical learning rates for optimization, (3) AutoAugment data augmentation strategy, (4) Large image size training (1024x1024 pixels), (5) Model ensembling. The training utilized both the competition dataset (31,072 images) and the public HPAv18 dataset (~78,000 images) to improve performance on rare classes. The final model achieved a macro F1 score of 0.593 on the private test set, winning first place among 2,172 teams. Training was performed on GPU hardware using PyTorch framework." \
  --keywords "transfer learning" \
  --keywords "fine-tuning" \
  --keywords "multi-label classification" \
  --keywords "Kaggle competition" \
  --keywords "DenseNet" \
  --keywords "Lovasz loss" \
  --keywords "AutoAugment" \
  --keywords "image classification" \
  --used-dataset "$HPA_DATASET_GUID" \
  --used-dataset "$IMAGENET_GUID" \
  --associated-publication "https://doi.org/10.1038/s41592-019-0658-6" \
  --additional-documentation "https://github.com/CellProfiling/HPA-competition")

echo "HPA training computation registered with GUID: $HPA_TRAINING_GUID"
echo ""

# -----------------------------------------------------------------------------
# Step 7: Register HPA DenseNet Model
# -----------------------------------------------------------------------------
echo "Step 7: Registering HPA DenseNet model..."

HPA_DENSENET_GUID=$(fairscape-cli rocrate register model "$ROCRATE_PATH" \
  --name "HPA DenseNet Subcellular Localization Classifier" \
  --author "Shubin Dai (Team bestfitting)" \
  --version "1.0" \
  --description "Winning model from the Human Protein Atlas Image Classification Kaggle competition. This DenseNet-121 based model classifies protein subcellular localization patterns in immunofluorescence microscopy images into 28 cellular compartment classes. The model handles the challenging multi-label classification problem where proteins can localize to multiple compartments simultaneously (1-6 labels per image). Key features: (1) DenseNet-121 backbone pretrained on ImageNet-1k, (2) Modified for 4-channel input (protein, microtubules, nucleus, ER), (3) Combined loss function with Lovasz loss for multi-label optimization, (4) Trained with AutoAugment data augmentation, (5) Input size of 1024x1024 pixels. The model achieved a macro F1 score of 0.593, representing a >20% improvement over previous methods (Loc-CAT: 0.47) and approaching expert human performance (0.71). The learned features can be used for image classification, pattern similarity measurement via feature extraction, or as pretrained weights for other biological imaging applications." \
  --keywords "DenseNet" \
  --keywords "protein localization" \
  --keywords "multi-label classification" \
  --keywords "Human Protein Atlas" \
  --keywords "subcellular localization" \
  --keywords "deep learning" \
  --keywords "confocal microscopy" \
  --keywords "transfer learning" \
  --keywords "Kaggle winner" \
  --content-url "https://modelzoo.cellprofiling.org" \
  --model-type "Convolutional Neural Network (DenseNet-121)" \
  --framework "PyTorch" \
  --model-format "PyTorch checkpoint" \
  --training-dataset "$HPA_DATASET_GUID" \
  --generated-by "$HPA_TRAINING_GUID" \
  --base-model "$DENSENET_GUID" \
  --input-size "1024x1024x4 (RGBY channels: protein, microtubules, nucleus, ER)" \
  --intended-use-case "Classification of protein subcellular localization patterns in immunofluorescence microscopy images. Can also be used for feature extraction to measure pattern similarity or as pretrained weights for biological image analysis tasks." \
  --usage-information "Input: 4-channel confocal microscopy images (green=protein, red=microtubules, blue=nucleus, yellow=ER). Output: Multi-label predictions for 28 subcellular localization classes with confidence scores. Recommended preprocessing: resize to 1024x1024, normalize to 8-bit." \
  --associated-publication "https://doi.org/10.1038/s41592-019-0658-6" \
  --url "https://modelzoo.cellprofiling.org" \
  --license "https://creativecommons.org/licenses/by/4.0/" \
  --citation "Ouyang, W., Winsnes, C.F., Hjelmare, M. et al. Analysis of the Human Protein Atlas Image Classification competition. Nat Methods 16, 1254-1261 (2019). https://doi.org/10.1038/s41592-019-0658-6")

echo "HPA DenseNet model registered with GUID: $HPA_DENSENET_GUID"
echo ""

# -----------------------------------------------------------------------------
# Step 8: Update relationships
# -----------------------------------------------------------------------------
echo "Step 8: Updating cross-references..."

# Update the HPA training computation to include the generated model
fairscape-cli rocrate register computation "$ROCRATE_PATH" \
  --guid "$HPA_TRAINING_GUID" \
  --name "HPA DenseNet Classification Model Training" \
  --run-by "Shubin Dai (Team bestfitting, Kaggle Competition Winner)" \
  --date-created "2019-01-10" \
  --description "Training computation for the winning HPA Image Classification model. The solution used DenseNet-121 as the backbone architecture, pretrained on ImageNet-1k, and fine-tuned on the HPA subcellular localization dataset. Key techniques employed: (1) Combined loss function with Lovasz loss term for multi-label classification, (2) Cyclical learning rates for optimization, (3) AutoAugment data augmentation strategy, (4) Large image size training (1024x1024 pixels), (5) Model ensembling. The training utilized both the competition dataset (31,072 images) and the public HPAv18 dataset (~78,000 images) to improve performance on rare classes. The final model achieved a macro F1 score of 0.593 on the private test set, winning first place among 2,172 teams. Training was performed on GPU hardware using PyTorch framework." \
  --keywords "transfer learning" \
  --keywords "fine-tuning" \
  --keywords "multi-label classification" \
  --keywords "Kaggle competition" \
  --keywords "DenseNet" \
  --keywords "Lovasz loss" \
  --keywords "AutoAugment" \
  --keywords "image classification" \
  --used-dataset "$HPA_DATASET_GUID" \
  --used-dataset "$IMAGENET_GUID" \
  --generated "$HPA_DENSENET_GUID" \
  --associated-publication "https://doi.org/10.1038/s41592-019-0658-6" \
  --additional-documentation "https://github.com/CellProfiling/HPA-competition"

echo "Cross-references updated."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "=== RO-Crate Creation Complete ==="
echo ""
echo "RO-Crate location: $ROCRATE_PATH"
echo ""
echo "Registered entities:"
echo "  Base Model (DenseNet121):     $DENSENET_GUID"
echo "  ImageNet-1k Dataset:          $IMAGENET_GUID"
echo "  DenseNet Training:            $TRAINING_COMP_GUID"
echo "  HPA Dataset:                  $HPA_DATASET_GUID"
echo "  HPA Model Training:           $HPA_TRAINING_GUID"
echo "  HPA DenseNet Model:           $HPA_DENSENET_GUID"
echo ""
echo "Provenance chain:"
echo "  ImageNet-1k --> [DenseNet Training] --> DenseNet121"
echo "                                              |"
echo "  HPA Dataset -----> [HPA Training] <--------+"
echo "                           |"
echo "                           v"
echo "                    HPA DenseNet Model"
echo ""
echo "To view the RO-Crate metadata:"
echo "  cat $ROCRATE_PATH/ro-crate-metadata.json"
echo ""
echo "To generate a datasheet:"
echo "  fairscape-cli build datasheet $ROCRATE_PATH"
echo ""
echo "To generate an evidence graph for the HPA DenseNet model:"
echo "  fairscape-cli build evidence-graph $ROCRATE_PATH $HPA_DENSENET_GUID"
echo ""
