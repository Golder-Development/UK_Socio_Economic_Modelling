"""
Analyze lexicon CSV files for potential conflicts and ambiguities.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path


def load_lexicon(filepath):
    """Load a lexicon CSV file and return list of entries."""
    entries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append({
                    'term': row['term'].strip(),
                    'weight': float(row['weight']),
                    'match_type': row['match_type'].strip(),
                    'source': row.get('source', '').strip(),
                    'notes': row.get('notes', '').strip()
                })
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return entries


def analyze_conflicts(lexicons_dir):
    """Analyze all lexicons for conflicts."""
    
    # Load all lexicons
    lexicons = {}
    lexicon_files = sorted([f for f in os.listdir(lexicons_dir) if f.endswith('.csv')])
    
    for filename in lexicon_files:
        filepath = os.path.join(lexicons_dir, filename)
        lexicon_name = filename.replace('.csv', '')
        entries = load_lexicon(filepath)
        lexicons[lexicon_name] = entries
        print(f"Loaded {lexicon_name}: {len(entries)} terms")
    
    print(f"\nTotal lexicons loaded: {len(lexicons)}\n")
    print("="*80)
    
    # Analysis 1: Cross-lexicon conflicts
    print("\n## 1. CROSS-LEXICON CONFLICTS")
    print("="*80)
    
    term_to_lexicons = defaultdict(list)
    for lexicon_name, entries in lexicons.items():
        for entry in entries:
            term = entry['term'].lower()
            term_to_lexicons[term].append({
                'lexicon': lexicon_name,
                'weight': entry['weight'],
                'match_type': entry['match_type'],
                'source': entry['source'],
                'notes': entry['notes']
            })
    
    cross_lexicon_conflicts = []
    for term, occurrences in term_to_lexicons.items():
        if len(occurrences) > 1:
            cross_lexicon_conflicts.append((term, occurrences))
    
    if cross_lexicon_conflicts:
        print(f"\nFound {len(cross_lexicon_conflicts)} terms appearing in multiple lexicons:\n")
        for term, occurrences in sorted(cross_lexicon_conflicts):
            print(f"\nTerm: '{term}'")
            print(f"  Appears in {len(occurrences)} lexicons:")
            for occ in occurrences:
                lexicon_short = occ['lexicon'].replace('L1_', '').replace('_', ' ')
                print(f"    - {lexicon_short}")
                print(f"      Weight: {occ['weight']}, Match type: {occ['match_type']}")
                if occ['notes']:
                    print(f"      Notes: {occ['notes']}")
            
            # Analyze why this is problematic
            weights = [occ['weight'] for occ in occurrences]
            positive_count = sum(1 for w in weights if w > 0)
            negative_count = sum(1 for w in weights if w < 0)
            
            if positive_count > 0 and negative_count > 0:
                print(f"  ⚠️  CRITICAL: Term has both positive and negative weights across lexicons!")
            elif len(set(weights)) > 1:
                print(f"  ⚠️  WARNING: Term has different weights: {set(weights)}")
            else:
                print(f"  ℹ️  INFO: Same weight across all lexicons, but may cause multi-classification")
    else:
        print("✓ No cross-lexicon conflicts found.")
    
    # Analysis 2: Within-lexicon conflicts (positive and negative weights)
    print("\n\n## 2. WITHIN-LEXICON CONFLICTS (Positive/Negative Weights)")
    print("="*80)
    
    within_conflicts = []
    for lexicon_name, entries in lexicons.items():
        term_weights = defaultdict(list)
        for entry in entries:
            term_weights[entry['term'].lower()].append({
                'weight': entry['weight'],
                'match_type': entry['match_type'],
                'notes': entry['notes']
            })
        
        for term, weights_list in term_weights.items():
            has_positive = any(w['weight'] > 0 for w in weights_list)
            has_negative = any(w['weight'] < 0 for w in weights_list)
            
            if has_positive and has_negative:
                within_conflicts.append({
                    'lexicon': lexicon_name,
                    'term': term,
                    'weights': weights_list
                })
    
    if within_conflicts:
        print(f"\nFound {len(within_conflicts)} terms with conflicting positive/negative weights in same lexicon:\n")
        for conflict in within_conflicts:
            print(f"\nLexicon: {conflict['lexicon'].replace('L1_', '').replace('_', ' ')}")
            print(f"  Term: '{conflict['term']}'")
            for w in conflict['weights']:
                print(f"    Weight: {w['weight']}, Match type: {w['match_type']}")
                if w['notes']:
                    print(f"    Notes: {w['notes']}")
            print(f"  ⚠️  CRITICAL: This term will both increase AND decrease the same classification score!")
    else:
        print("✓ No within-lexicon positive/negative conflicts found.")
    
    # Analysis 3: Exact duplicates within same lexicon
    print("\n\n## 3. EXACT DUPLICATES WITHIN SAME LEXICON")
    print("="*80)
    
    duplicates = []
    for lexicon_name, entries in lexicons.items():
        term_entries = defaultdict(list)
        for entry in entries:
            term_entries[entry['term'].lower()].append(entry)
        
        for term, entry_list in term_entries.items():
            if len(entry_list) > 1:
                # Check if they're truly identical or have different attributes
                unique_entries = []
                for entry in entry_list:
                    key = (entry['weight'], entry['match_type'], entry['source'])
                    if key not in [
                        (e['weight'], e['match_type'], e['source']) 
                        for e in unique_entries
                    ]:
                        unique_entries.append(entry)
                
                if len(entry_list) > len(unique_entries):
                    duplicates.append({
                        'lexicon': lexicon_name,
                        'term': term,
                        'count': len(entry_list),
                        'entries': entry_list
                    })
    
    if duplicates:
        print(f"\nFound {len(duplicates)} exact duplicate terms:\n")
        for dup in duplicates:
            print(f"\nLexicon: {dup['lexicon'].replace('L1_', '').replace('_', ' ')}")
            print(f"  Term: '{dup['term']}'")
            print(f"  Appears {dup['count']} times:")
            for entry in dup['entries']:
                print(f"    Weight: {entry['weight']}, Match type: {entry['match_type']}")
                if entry['notes']:
                    print(f"    Notes: {entry['notes']}")
            print(f"  ⚠️  WARNING: Duplicate entries will multiply the weight contribution!")
    else:
        print("✓ No exact duplicates found within lexicons.")
    
    # Analysis 4: Semantic overlaps and substring conflicts
    print("\n\n## 4. SEMANTIC OVERLAPS & SUBSTRING CONFLICTS")
    print("="*80)
    
    # Find substring terms that might overlap
    substring_conflicts = []
    
    for lexicon_name, entries in lexicons.items():
        substrings = [e for e in entries if e['match_type'] == 'substring']
        tokens = [e for e in entries if e['match_type'] == 'token']
        phrases = [e for e in entries if e['match_type'] == 'phrase']
        
        # Check if any substring could match a token/phrase
        for sub in substrings:
            sub_term = sub['term'].lower()
            for token in tokens:
                token_term = token['term'].lower()
                if sub_term in token_term and sub_term != token_term:
                    substring_conflicts.append({
                        'lexicon': lexicon_name,
                        'substring': sub,
                        'matched_term': token,
                        'type': 'token'
                    })
            for phrase in phrases:
                phrase_term = phrase['term'].lower()
                if sub_term in phrase_term:
                    substring_conflicts.append({
                        'lexicon': lexicon_name,
                        'substring': sub,
                        'matched_term': phrase,
                        'type': 'phrase'
                    })
    
    if substring_conflicts:
        print(f"\nFound {len(substring_conflicts)} potential substring overlaps:\n")
        for conflict in substring_conflicts:
            print(f"\nLexicon: {conflict['lexicon'].replace('L1_', '').replace('_', ' ')}")
            print(f"  Substring: '{conflict['substring']['term']}' (weight: {conflict['substring']['weight']})")
            print(f"  Matches {conflict['type']}: '{conflict['matched_term']['term']}' (weight: {conflict['matched_term']['weight']})")
            print(f"  ℹ️  INFO: Both could match the same text, causing double-counting")
    else:
        print("✓ No obvious substring conflicts found.")
    
    # Analysis 5: Problematic negative weight patterns
    print("\n\n## 5. NEGATIVE WEIGHT EXCLUSION PATTERNS")
    print("="*80)
    
    all_negatives = []
    for lexicon_name, entries in lexicons.items():
        negatives = [e for e in entries if e['weight'] < 0]
        if negatives:
            all_negatives.append({
                'lexicon': lexicon_name,
                'terms': negatives
            })
    
    if all_negatives:
        print(f"\nFound {len(all_negatives)} lexicons with negative weight exclusions:\n")
        for lex in all_negatives:
            print(f"\n{lex['lexicon'].replace('L1_', '').replace('_', ' ')}:")
            for term in lex['terms']:
                print(f"  '{term['term']}' (weight: {term['weight']})")
                if term['notes']:
                    print(f"    Notes: {term['notes']}")
        print("\n  ℹ️  INFO: Negative weights are exclusion patterns. Ensure they don't")
        print("     over-penalize cases that legitimately belong to the category.")
    else:
        print("✓ No negative weight exclusions found.")
    
    # Summary statistics
    print("\n\n## 6. SUMMARY STATISTICS")
    print("="*80)
    
    total_terms = sum(len(entries) for entries in lexicons.values())
    unique_terms = len(term_to_lexicons)
    
    print(f"\nTotal terms across all lexicons: {total_terms}")
    print(f"Unique terms: {unique_terms}")
    print(f"Terms appearing in multiple lexicons: {len(cross_lexicon_conflicts)}")
    print(f"Within-lexicon conflicts: {len(within_conflicts)}")
    print(f"Exact duplicates: {len(duplicates)}")
    print(f"Substring overlaps: {len(substring_conflicts)}")
    
    # Calculate overlap percentage
    overlap_pct = (len(cross_lexicon_conflicts) / unique_terms * 100) if unique_terms > 0 else 0
    print(f"Cross-lexicon overlap rate: {overlap_pct:.1f}%")
    
    print("\n" + "="*80)
    print("\nANALYSIS COMPLETE")
    print("="*80)


if __name__ == '__main__':
    lexicons_dir = Path(__file__).parent / 'lexicons'
    analyze_conflicts(lexicons_dir)
