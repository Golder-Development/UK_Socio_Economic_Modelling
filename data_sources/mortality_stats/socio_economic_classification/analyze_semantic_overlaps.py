"""
Enhanced semantic overlap analysis - check for related terms that might cause ambiguity.
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


def analyze_semantic_overlaps(lexicons_dir):
    """Find terms that might cause semantic ambiguity across lexicons."""
    
    # Load all lexicons
    lexicons = {}
    lexicon_files = sorted([f for f in os.listdir(lexicons_dir) if f.endswith('.csv')])
    
    for filename in lexicon_files:
        filepath = os.path.join(lexicons_dir, filename)
        lexicon_name = filename.replace('.csv', '')
        entries = load_lexicon(filepath)
        lexicons[lexicon_name] = entries
    
    print("="*80)
    print("SEMANTIC OVERLAP ANALYSIS")
    print("="*80)
    
    # Analysis 1: Terms with shared roots/stems
    print("\n## 1. TERMS WITH SHARED ROOTS (Cross-Lexicon)")
    print("="*80)
    
    # Group terms by potential root words
    root_patterns = {
        'tubercul': ['tuberculosis', 'tuberculous', 'tubercul'],
        'phthisis': ['phthisis'],
        'pneumo': ['pneumonia', 'pneumococc'],
        'cancer/carcinoma': ['cancer', 'carcinoma', 'malignant'],
        'chronic': ['chronic'],
        'cirrhosis': ['cirrhosis'],
        'heart': ['heart', 'cardiac', 'myocarditis', 'endocarditis', 'pericarditis'],
        'poison': ['poison', 'toxic'],
        'suicide': ['suicide', 'suicides', 'self harm', 'self inflicted'],
        'respiratory': ['respiratory', 'bronchitis', 'pneumonia', 'asthma'],
        'maternal': ['maternal', 'puerperal', 'pregnancy', 'childbirth'],
        'congenital': ['congenital', 'malformation', 'deformity'],
        'infection': ['infection', 'infectious', 'septic', 'septicaemia'],
    }
    
    found_overlaps = []
    
    for root_name, root_terms in root_patterns.items():
        lexicon_matches = defaultdict(list)
        
        for lexicon_name, entries in lexicons.items():
            for entry in entries:
                term_lower = entry['term'].lower()
                for root_term in root_terms:
                    if root_term in term_lower:
                        lexicon_matches[lexicon_name].append(entry)
                        break
        
        if len(lexicon_matches) > 1:
            found_overlaps.append((root_name, lexicon_matches))
    
    if found_overlaps:
        print(f"\nFound {len(found_overlaps)} root patterns appearing across multiple lexicons:\n")
        for root_name, matches in found_overlaps:
            print(f"\n🔍 Root pattern: '{root_name}'")
            print(f"   Appears in {len(matches)} lexicons:")
            for lexicon, entries in matches.items():
                print(f"\n   📁 {lexicon.replace('L1_', '').replace('_', ' ')}:")
                for entry in entries:
                    print(f"      • '{entry['term']}' (weight: {entry['weight']}, {entry['match_type']})")
            
            # Check if weights differ
            all_weights = [e['weight'] for entries in matches.values() for e in entries]
            if len(set(all_weights)) > 1:
                print(f"   ⚠️  Different weights used: {set(all_weights)}")
    else:
        print("✓ No cross-lexicon semantic overlaps detected.")
    
    # Analysis 2: Check for ambiguous disease classifications
    print("\n\n## 2. POTENTIALLY AMBIGUOUS DISEASE TERMS")
    print("="*80)
    
    ambiguous_terms = [
        'cirrhosis',  # Could be chronic disease or substance use
        'pneumonia',  # Could be infectious or respiratory
        'phthisis',   # Could be infectious (TB) or chronic wasting
        'asphyxia',   # Could be accidental or violence
        'poisoning',  # Could be accidental, self-harm, or homicide
        'burn',       # Could be accidental or violence
    ]
    
    print("\nChecking for terms that could belong to multiple categories:\n")
    
    for ambiguous in ambiguous_terms:
        found_in = []
        for lexicon_name, entries in lexicons.items():
            for entry in entries:
                if ambiguous in entry['term'].lower():
                    found_in.append({
                        'lexicon': lexicon_name,
                        'entry': entry
                    })
        
        if found_in:
            print(f"\n🔍 Term containing '{ambiguous}':")
            if len(found_in) == 1:
                lex = found_in[0]
                print(f"   ✓ Only in: {lex['lexicon'].replace('L1_', '').replace('_', ' ')}")
                print(f"      '{lex['entry']['term']}' (weight: {lex['entry']['weight']})")
            else:
                print(f"   ⚠️  Found in {len(found_in)} lexicons:")
                for item in found_in:
                    print(f"      • {item['lexicon'].replace('L1_', '').replace('_', ' ')}")
                    print(f"        '{item['entry']['term']}' (weight: {item['entry']['weight']})")
    
    # Analysis 3: Regex patterns that might be too broad
    print("\n\n## 3. BROAD REGEX PATTERNS")
    print("="*80)
    
    print("\nChecking for regex patterns that might match too broadly:\n")
    
    for lexicon_name, entries in lexicons.items():
        regex_entries = [e for e in entries if e['match_type'] == 'regex']
        if regex_entries:
            print(f"\n📁 {lexicon_name.replace('L1_', '').replace('_', ' ')}:")
            for entry in regex_entries:
                print(f"   • Pattern: '{entry['term']}'")
                print(f"     Weight: {entry['weight']}, Notes: {entry.get('notes', 'N/A')}")
                print(f"     ⚠️  Regex patterns can match broadly - verify specificity")
    
    # Analysis 4: High-weight terms analysis
    print("\n\n## 4. HIGH-WEIGHT TERMS (Weight >= 9)")
    print("="*80)
    
    print("\nHigh-weight terms that strongly indicate a category:\n")
    
    high_weight_by_lexicon = defaultdict(list)
    
    for lexicon_name, entries in lexicons.items():
        for entry in entries:
            if entry['weight'] >= 9:
                high_weight_by_lexicon[lexicon_name].append(entry)
    
    for lexicon_name, high_terms in sorted(high_weight_by_lexicon.items()):
        print(f"\n📁 {lexicon_name.replace('L1_', '').replace('_', ' ')} ({len(high_terms)} terms):")
        for term in sorted(high_terms, key=lambda x: -x['weight']):
            print(f"   • '{term['term']}' (weight: {term['weight']}, {term['match_type']})")
    
    # Analysis 5: Low-weight generic terms
    print("\n\n## 5. LOW-WEIGHT GENERIC TERMS (Weight <= 5)")
    print("="*80)
    
    print("\nLow-weight terms that weakly suggest a category:\n")
    
    low_weight_terms = []
    for lexicon_name, entries in lexicons.items():
        for entry in entries:
            if 0 < entry['weight'] <= 5:
                low_weight_terms.append({
                    'lexicon': lexicon_name,
                    'entry': entry
                })
    
    if low_weight_terms:
        print(f"\nFound {len(low_weight_terms)} low-weight terms:")
        for item in low_weight_terms[:20]:  # Show first 20
            print(f"   • '{item['entry']['term']}' in {item['lexicon'].replace('L1_', '').replace('_', ' ')}")
            print(f"     Weight: {item['entry']['weight']}, {item['entry']['match_type']}")
        if len(low_weight_terms) > 20:
            print(f"   ... and {len(low_weight_terms) - 20} more")
        print("\n   ℹ️  Low weights might not be decisive enough for classification")
    
    # Analysis 6: Check substring terms
    print("\n\n## 6. SUBSTRING MATCH ANALYSIS")
    print("="*80)
    
    print("\nSubstring matches can be powerful but risky:\n")
    
    for lexicon_name, entries in lexicons.items():
        substrings = [e for e in entries if e['match_type'] == 'substring']
        if substrings:
            print(f"\n📁 {lexicon_name.replace('L1_', '').replace('_', ' ')}:")
            for sub in substrings:
                print(f"   • '{sub['term']}' (weight: {sub['weight']})")
                print(f"     Will match any term containing this substring")
                if sub['notes']:
                    print(f"     Notes: {sub['notes']}")
    
    print("\n" + "="*80)
    print("SEMANTIC ANALYSIS COMPLETE")
    print("="*80)


if __name__ == '__main__':
    lexicons_dir = Path(__file__).parent / 'lexicons'
    analyze_semantic_overlaps(lexicons_dir)
