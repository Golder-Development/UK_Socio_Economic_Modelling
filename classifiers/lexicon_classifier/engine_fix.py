# This is the correct section that should replace lines 135-155

        rows = []
        for _, r in df.iterrows():
            term = str(r[settings.LEXICON_SCHEMA["term_column"]]).strip()
            weight = int(r[settings.LEXICON_SCHEMA["weight_column"]])
            match_type = str(r[settings.LEXICON_SCHEMA["match_type_column"]]).strip().lower()

            # Validate match type
            if match_type not in settings.VALID_MATCH_TYPES:
                raise ValueError(
                    f"Invalid match_type '{match_type}' in {fn}. "
                    f"Must be one of: {settings.VALID_MATCH_TYPES}"
                )

            # Normalize lexicon terms using the same normalization as input text
            # This ensures phrases like "cirrhosis of liver (alcoholic)" match correctly
            term = normalize_text(term, settings.TEXT_NORMALIZATION)

            rows.append({
                "term": term,
                "weight": weight,
                "match_type": match_type,
            })
