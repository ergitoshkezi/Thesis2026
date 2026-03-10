"""
Comparison — Token-Level File Diff & Matching
================================================

Functions for comparing two log files at the token level,
identifying differences and matching rows across files.

Author : Ergito Shkëzi
Project: Master's Thesis 2026
"""

# ──────────────────────────────────────────────────────────────────────
# Third-Party Libraries
# ──────────────────────────────────────────────────────────────────────
from nltk.tokenize import word_tokenize


# ══════════════════════════════════════════════════════════════════════
#  Token-Level Diff
# ══════════════════════════════════════════════════════════════════════


def find_matching_sublists(file_, e, diff_rows):
    """Find which extra rows from *e* exist in *file_* at *diff_rows* positions.

    Returns (marked_e, index_found) where each element of *marked_e*
    is prefixed with [FOUND] or [NOT FOUND].
    """
    file_dict = {i: " ".join(file_[i].split()[3:]) for i in diff_rows if 0 <= i < len(file_)}

    marked_e = []
    index_found = []

    # Process elements in e and compare to file_dict for a match
    for index, row in enumerate(e):
        e_content = " ".join(row.split()[3:])
        found = False

        # Check against the indices specified in diff_rows
        for i, f_content in file_dict.items():
            if e_content == f_content:
                marked_e.append(f"[FOUND] {file_[i]}")
                index_found.append(i)
                found = True
                break

        if not found:
            marked_e.append(f"[NOT FOUND] {row}")

    return marked_e, index_found


def tokenize(file1, file2,row,diff_rows):
    """Token-level diff of two log lines, marking differences with @@ markers.

    Returns (result_string, diff_rows, flag) where *flag* is True when
    the row is completely different.
    """
    s_eq = []
    s_dots= []
    tokens1 = word_tokenize(file1)[3:]
    tokens2 = word_tokenize(file2)[3:]
    for num,i in enumerate(tokens2):
        if i == "=":
            s_eq.append(num)
        if i == ":":
            s_dots.append(num)

    tokens1 = [token for token in word_tokenize(file1)[3:] if token not in ('=', ':')]
    tokens2 = [token for token in word_tokenize(file2)[3:] if token not in ('=', ':')]
    c=0
    flag=False
    max_length = max(len(tokens1), len(tokens2))
    final_tokens = []
    

    for i in range(max_length):
        if i < len(tokens1) and i < len(tokens2):
            if tokens1[i] != tokens2[i]:
                c+=1
                if row not in diff_rows:
                    diff_rows.append(row)
                # Mark the differing token from tokens2
                marked_token = f'@@{tokens2[i]}@@'
                final_tokens.append(marked_token)
            else:
                final_tokens.append(tokens2[i])
        elif i < len(tokens2):
            # Extra tokens in tokens2
            marked_token = f'@@{tokens2[i]}@@'
            final_tokens.append(marked_token)
        elif i < len(tokens1):
            marked_token = f'@@{tokens1[i]}@@'
            ####attenzione implementare per file 1  i extra token della riga 

    if c == len(tokens1) or c == len(tokens2):
        flag=True # The row is completly different  ->True

    for item in s_eq:
        final_tokens.insert(item,"=")
    for item in s_dots:
        final_tokens.insert(item,":")
            
    result = ' '.join(final_tokens)
    return result,diff_rows,flag
