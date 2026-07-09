# Dual-energy-Algorithm
A GC-MS non-targeted analysis workflow algorithm that pairs high-energy and low-energy spectra only by retaining constraints on retention time and spectral similarity, providing evidence for molecular ion peaks while maintaining compatibility with traditional library matching.
STEP 1: Convert the CEF file exported from the unknown compound analysis software into Excel.
Input: High-energy CEF file
Output: High-energy Excel file

STEP 2: Insert the match score, signal-to-noise ratio, peak area, and peak height directly exported from the unknown compound analysis software into the above file. The exported CSV file must first be saved as UTF-8 format.
Input: Software-exported CSV file; high-energy Excel file
Output: Full-information high-energy Excel file

STEP 3: Match the high-energy and low-energy data based on the retention time window.
Input: Full-information high-energy Excel file; low-energy CEF file
Output: High-low energy one-to-many file

STEP 4: Calculate Jaccard similarity and retain the best match.
Input: High-energy one-to-many file
Output: High-energy one-to-one file and complete records
