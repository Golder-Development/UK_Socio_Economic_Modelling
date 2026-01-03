"""
Manual Overrides Handler
-------------------------

Handles manual classification overrides for missing ICD codes.

This module provides functionality to:
1. Load manual override definitions from CSV
2. Apply overrides to fill missing data (NOT replace existing data)
3. Validate and report on override usage

CRITICAL: This system fills gaps only. It never overwrites existing classifications.

Author: Paul Golder (Hysnap)
"""

from __future__ import annotations

import os
from typing import Dict, Any
import pandas as pd


class ManualOverridesHandler:
    """Handler for manual ICD code overrides."""

    def __init__(self, overrides_path: str, settings: Any):
        """
        Initialize the manual overrides handler.

        Args:
            overrides_path: Path to manual_overrides.csv file
            settings: Settings module containing configuration
        """
        self.overrides_path = overrides_path
        self.settings = settings
        self.overrides_df = None
        self.applied_count = 0
        self.skipped_count = 0
        
        if os.path.exists(overrides_path):
            self._load_overrides()
        else:
            print(f"NOTE: No manual overrides file found at {overrides_path}")
            self.overrides_df = pd.DataFrame()

    def _load_overrides(self):
        """Load and validate manual overrides from CSV."""
        try:
            self.overrides_df = pd.read_csv(self.overrides_path)
            
            # Validate required columns
            required_cols = [
                'icd_version', 'icd_code', 'cause_description',
                'L1_category', 'confidence', 'reason', 'date_added'
            ]
            missing_cols = [c for c in required_cols if c not in self.overrides_df.columns]
            
            if missing_cols:
                raise ValueError(
                    f"Manual overrides file missing required columns: {missing_cols}"
                )
            
            # Validate L1 categories
            valid_categories = set(self.settings.TAXONOMY.keys())
            invalid_cats = self.overrides_df[
                ~self.overrides_df['L1_category'].isin(valid_categories)
            ]
            
            if len(invalid_cats) > 0:
                raise ValueError(
                    f"Manual overrides contain invalid L1 categories:\n"
                    f"{invalid_cats[['icd_code', 'L1_category']].to_string()}"
                )
            
            # Validate confidence levels
            valid_confidence = {'high', 'medium', 'low'}
            invalid_conf = self.overrides_df[
                ~self.overrides_df['confidence'].isin(valid_confidence)
            ]
            
            if len(invalid_conf) > 0:
                raise ValueError(
                    f"Manual overrides contain invalid confidence levels:\n"
                    f"{invalid_conf[['icd_code', 'confidence']].to_string()}"
                )
            
            # Normalize version and code columns for matching
            self.overrides_df['icd_version'] = (
                self.overrides_df['icd_version'].astype(str).str.strip().str.upper()
            )
            self.overrides_df['icd_code'] = (
                self.overrides_df['icd_code'].astype(str).str.strip()
            )
            
            print(f"Loaded {len(self.overrides_df)} manual override(s) from {self.overrides_path}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load manual overrides: {e}")

    def inject_missing_codes(
        self,
        df: pd.DataFrame,
        target_version: str = None
    ) -> pd.DataFrame:
        """
        Inject completely missing codes from manual overrides as new rows.
        
        This handles codes that don't exist in the source data at all.
        
        Args:
            df: Input dataframe
            target_version: If specified, only inject codes for this ICD version.
                           If None, auto-detects version from dataframe (uses most common version)
            
        Returns:
            Dataframe with missing codes injected as new rows
        """
        if self.overrides_df is None or len(self.overrides_df) == 0:
            return df
        
        df = df.copy()
        code_col = self.settings.DEFAULT_COLUMNS["code"]
        desc_col = self.settings.DEFAULT_COLUMNS["description"]
        version_col = self.settings.DEFAULT_COLUMNS["version"]
        
        # Auto-detect version if not specified
        if target_version is None and len(df) > 0:
            # Get the most common version in the dataframe
            versions = df[version_col].astype(str).str.strip().str.upper()
            if len(versions.unique()) == 1:
                target_version = versions.iloc[0]
                print(f"  [Manual Overrides] Auto-detected version: {target_version}")
            else:
                # Multiple versions - don't inject to avoid cross-contamination
                print(f"  [Manual Overrides] Multiple versions detected, skipping injection")
                return df
        
        # Filter overrides by target version
        overrides_to_inject = self.overrides_df.copy()
        if target_version:
            target_version_norm = str(target_version).strip().upper()
            overrides_to_inject = overrides_to_inject[
                overrides_to_inject['icd_version'] == target_version_norm
            ]
        
        if len(overrides_to_inject) == 0:
            return df
        
        # Normalize existing codes for comparison
        df['_norm_version'] = df[version_col].astype(str).str.strip().str.upper()
        df['_norm_code'] = df[code_col].astype(str).str.strip()
        df['_match_key'] = df['_norm_version'] + '||' + df['_norm_code']
        
        # Find overrides that don't exist in the dataframe
        overrides_to_inject['_match_key'] = (
            overrides_to_inject['icd_version'] + '||' + overrides_to_inject['icd_code']
        )
        missing_overrides = overrides_to_inject[
            ~overrides_to_inject['_match_key'].isin(df['_match_key'])
        ]
        
        injected_count = 0
        if len(missing_overrides) > 0:
            # Create new rows for missing codes
            new_rows = []
            for _, override in missing_overrides.iterrows():
                new_row = {
                    code_col: override['icd_code'],
                    version_col: override['icd_version'],
                    desc_col: override['cause_description'],
                    '_manual_override': True,
                    '_manual_category': override['L1_category'],
                    '_manual_confidence': override['confidence'],
                    '_manual_reason': override['reason']
                }
                new_rows.append(new_row)
                injected_count += 1
            
            # Append new rows to dataframe
            new_rows_df = pd.DataFrame(new_rows)
            df = pd.concat([df, new_rows_df], ignore_index=True)
            
            print(f"  [Manual Overrides] Injected {injected_count} missing code(s)")
        
        # Clean up temporary columns
        df.drop(columns=['_norm_version', '_norm_code', '_match_key'], inplace=True, errors='ignore')
        
        return df

    def apply_to_dataframe(
        self,
        df: pd.DataFrame,
        fill_missing_only: bool = True,
        inject_missing: bool = True
    ) -> pd.DataFrame:
        """
        Apply manual overrides to a dataframe.

        This method:
        1. Injects completely missing codes as new rows (if inject_missing=True)
        2. Fills missing data for existing codes (if fill_missing_only=True)

        Args:
            df: Input dataframe with ICD codes
            fill_missing_only: If True (default), only fill missing codes.
                               If False, will overwrite existing data (NOT RECOMMENDED)
            inject_missing: If True (default), inject missing codes as new rows

        Returns:
            Dataframe with manual overrides applied
        """
        if self.overrides_df is None or len(self.overrides_df) == 0:
            return df
        
        # Step 1: Inject completely missing codes as new rows
        if inject_missing:
            df = self.inject_missing_codes(df)
        
        df = df.copy()
        
        # Ensure we have the required columns
        code_col = self.settings.DEFAULT_COLUMNS["code"]
        desc_col = self.settings.DEFAULT_COLUMNS["description"]
        version_col = self.settings.DEFAULT_COLUMNS["version"]
        
        # Normalize version and code for matching
        df['_norm_version'] = df[version_col].astype(str).str.strip().str.upper()
        df['_norm_code'] = df[code_col].astype(str).str.strip()
        
        # Create matching key
        df['_match_key'] = df['_norm_version'] + '||' + df['_norm_code']
        overrides_match_key = (
            self.overrides_df['icd_version'] + '||' + self.overrides_df['icd_code']
        )
        
        # Identify which overrides might apply
        applicable_overrides = self.overrides_df[
            overrides_match_key.isin(df['_match_key'])
        ].copy()
        applicable_overrides['_match_key'] = (
            applicable_overrides['icd_version'] + '||' + applicable_overrides['icd_code']
        )
        
        if len(applicable_overrides) == 0:
            # Clean up temporary columns
            df.drop(columns=['_norm_version', '_norm_code', '_match_key'], inplace=True)
            return df
        
        # Apply overrides
        self.applied_count = 0
        self.skipped_count = 0
        
        for idx, row in df.iterrows():
            match_key = row['_match_key']
            override = applicable_overrides[
                applicable_overrides['_match_key'] == match_key
            ]
            
            if len(override) == 0:
                continue
            
            if len(override) > 1:
                print(
                    f"WARNING: Multiple manual overrides found for "
                    f"{row[version_col]} {row[code_col]}. Using first match."
                )
            
            override = override.iloc[0]
            
            # Check if we should apply the override
            if fill_missing_only:
                # Only apply if description is missing or empty
                current_desc = str(row[desc_col]) if pd.notna(row[desc_col]) else ''
                if current_desc.strip() and current_desc.lower() not in ['nan', 'none', '']:
                    self.skipped_count += 1
                    continue
            
            # Apply the override
            df.at[idx, desc_col] = override['cause_description']
            df.at[idx, '_manual_override'] = True
            df.at[idx, '_manual_category'] = override['L1_category']
            df.at[idx, '_manual_confidence'] = override['confidence']
            df.at[idx, '_manual_reason'] = override['reason']
            self.applied_count += 1
        
        # Clean up temporary columns
        df.drop(columns=['_norm_version', '_norm_code', '_match_key'], inplace=True)
        
        return df

    def apply_classifications(
        self,
        classified_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Apply manual classifications to already-classified dataframe.

        This is called AFTER lexicon classification to ensure manual overrides
        for missing codes get their pre-defined classifications applied.

        Args:
            classified_df: Dataframe after lexicon classification

        Returns:
            Dataframe with manual classifications applied where appropriate
        """
        if '_manual_override' not in classified_df.columns:
            return classified_df
        
        df = classified_df.copy()
        
        # Apply manual classifications where override flag is set
        manual_mask = df['_manual_override'].fillna(False).astype(bool)
        
        if manual_mask.sum() > 0:
            df.loc[manual_mask, self.settings.OUTPUT_COLUMNS['category_code']] = (
                df.loc[manual_mask, '_manual_category']
            )
            df.loc[manual_mask, self.settings.OUTPUT_COLUMNS['category_name']] = (
                df.loc[manual_mask, '_manual_category'].map(self.settings.TAXONOMY)
            )
            df.loc[manual_mask, self.settings.OUTPUT_COLUMNS['confidence']] = (
                df.loc[manual_mask, '_manual_confidence']
            )
            
            # Add manual flag to output
            df.loc[manual_mask, 'manual_classification'] = True
            df.loc[manual_mask, 'manual_reason'] = df.loc[manual_mask, '_manual_reason']
        
        # Clean up temporary columns
        temp_cols = ['_manual_override', '_manual_category', '_manual_confidence', '_manual_reason']
        df.drop(columns=[c for c in temp_cols if c in df.columns], inplace=True)
        
        return df

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about override application.

        Returns:
            Dictionary with application statistics
        """
        return {
            'total_overrides_defined': len(self.overrides_df) if self.overrides_df is not None else 0,
            'overrides_applied': self.applied_count,
            'overrides_skipped': self.skipped_count,
        }

    def print_summary(self):
        """Print a summary of override application."""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("Manual Overrides Summary")
        print("=" * 60)
        print(f"Total overrides defined:     {stats['total_overrides_defined']}")
        print(f"Overrides applied:           {stats['overrides_applied']}")
        print(f"Overrides skipped (exists):  {stats['overrides_skipped']}")
        print("=" * 60)


def load_and_apply_overrides(
    df: pd.DataFrame,
    overrides_path: str,
    settings: Any,
    fill_missing_only: bool = True
) -> tuple[pd.DataFrame, ManualOverridesHandler]:
    """
    Convenience function to load and apply manual overrides.

    Args:
        df: Input dataframe
        overrides_path: Path to manual overrides CSV
        settings: Settings module
        fill_missing_only: Only fill missing codes (default True)

    Returns:
        Tuple of (modified_dataframe, handler_instance)
    """
    handler = ManualOverridesHandler(overrides_path, settings)
    df = handler.apply_to_dataframe(df, fill_missing_only=fill_missing_only)
    return df, handler
