import pandas as pd
import os
import ast

def jaccard_similarity(peaks1, peaks2, tolerance=0.005):
    mz1 = {mz for mz, _ in peaks1}
    mz2 = {mz for mz, _ in peaks2}
    intersection = {mz for mz in mz1 if any(abs(mz - mz2_val) <= tolerance for mz2_val in mz2)}
    union = mz1.union(mz2)
    similarity = len(intersection) / len(union) if union else 0.0
    return round(similarity, 6)


def select_best_low(group):

    max_jaccard = group['Jaccard Similarity'].max()
    candidates = group[group['Jaccard Similarity'] == max_jaccard]

    best_idx = candidates['low a'].idxmax()
    if pd.isna(best_idx):
        return None

    return group.loc[best_idx]



def process_single_excel(file_path, output_folder):
    df = pd.read_excel(file_path)
    print (df.dtypes)
    print(df['low MSPeaks'].head(3))
    print(type(df['low MSPeaks'].iloc[0]))


    def safe_literal_eval(val):
        if isinstance(val, str) and val != 'nan':
            try:
                return ast.literal_eval(val)
            except (ValueError, SyntaxError):
                return []
        else:
            return []


    df['low MSPeaks'] = df['low MSPeaks'].apply(safe_literal_eval)
    df['high MSPeaks'] = df['high MSPeaks'].apply(safe_literal_eval)  #

    df['Jaccard Similarity'] = df.apply(lambda row: jaccard_similarity(row['high MSPeaks'], row['low MSPeaks']), axis=1)
    print(df[['high a', 'low a', 'Jaccard Similarity']].isna().sum())
    print(df[['high a', 'low a', 'Jaccard Similarity']].head(10))

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"output {output_folder} ")


    all_score_file = os.path.join(output_folder, f"processed_all_with_score_{os.path.basename(file_path)}")
    df.to_excel(all_score_file, index=False)
    print(f"saved {all_score_file}")


    best_df = df.groupby(['high a'], group_keys=False).apply(select_best_low).reset_index(drop=True)


    best_file = os.path.join(output_folder, f"processed_best_{os.path.basename(file_path)}")
    best_df.to_excel(best_file, index=False)
    print(f"matched HE-LE（Jaccard + low a）saved at {best_file}")


def process_all_excel_files(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"output {output_folder} created")

    for file_name in os.listdir(input_folder):
        if file_name.endswith(('.xlsx', '.xls')):
            file_path = os.path.join(input_folder, file_name)
            print(f"doing {file_name} ...")
            process_single_excel(file_path, output_folder)


# 使用示例
input_folder = r".\The output folder path from step 3"
output_folder = r".\The output folder path of step 4"

process_all_excel_files(input_folder, output_folder)
