# Met-db

### image registration for raw data
**FFT**
>Phase Correlation:
Peak Detection: When you calculate the phase correlation between two images, the peak of the resulting image represents the translational shift between them. This peak is very distinct and can be detected easily, even in the presence of noise.
Subpixel Accuracy: Phase correlation can provide subpixel accuracy, making it more precise than many spatial domain methods.

 Appendix
### Phase Correlation Principle

Phase correlation is a technique in the frequency domain used to estimate the relative translative offset between two images. This method is widely utilized in image registration due to its efficiency and robustness against intensity variations and noise.

#### 1. Fourier Transforms

Compute the discrete Fourier transforms (DFT) of the two images that are to be registered:

- For Image 1: $F1(u, v)$
- For Image 2: $F2(u, v)$

#### 2. Cross-Power Spectrum

Determine the cross-power spectrum of the Fourier transforms of the two images. The formula is:

$ R(u, v) = \frac{F1(u, v) \times F2^*(u, v)}{|F1(u, v) \times F2^*(u, v)|} $

Here, $F2^*$ represents the complex conjugate of $F2$.

#### 3. Inverse Fourier Transform

Next, compute the inverse Fourier transform of the cross-power spectrum  $R(u, v)$. This translates the data back into the spatial domain.

#### 4. Peak Detection

The location of the peak in this spatial domain indicates the translational shift between the two images. If there's no rotation or scaling, this peak precisely reveals the translation coordinates between the images.

### Rationale

- The **cross-power spectrum** (in step 2) works to eliminate amplitude data, focusing solely on phase differences. The calculation of $F1 \times F2^*$ provides the phase difference for every frequency component. By dividing it by its magnitude, the result is normalized, keeping only phase data.

- With the inverse Fourier transform (in step 3), spatial shifts appear as peaks. The location of the largest peak equates to the relative shift between the images.


Note: Phase correlation assumes that there's only translational motion between the two images. Any rotations, scalings, or non-linear transformations would need additional considerations or preprocessing.
