import spacy
from setup.icd_client import IcdApiClient
from typing import List, Dict, Any

# --- spaCy Model Loading (Corrected) ---
# It's more efficient to load this heavy model once when the module is imported,
# rather than every time an object is created.
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("="*50)
    print("ERROR: Spacy model 'en_core_web_md' not found.")
    print("Please run this command in your terminal to download it:")
    print("python -m spacy download en_core_web_md")
    print("="*50)
    nlp = None

class MappingSuggester:
    """
    An intelligent service to suggest ICD-11 mappings for NAMASTE terms
    using NLP and semantic similarity.
    """
    def __init__(self, icd_client: IcdApiClient):
        """
        Initializes the suggester with an active ICD API client.
        """
        if nlp is None:
            raise RuntimeError(
                "spaCy model 'en_core_web_md' is not loaded. "
                "The program cannot continue. Please download the model."
            )
        self.icd_client = icd_client
        self.similarity_weight = 0.7
        self.keyword_weight = 0.3

    def _calculate_similarity_score(self, text1: str, text2: str) -> float:
        """
        Calculates the semantic similarity between two texts.
        """
        if not text1 or not text2:
            return 0.0
        
        # FIX: This now correctly uses the globally loaded 'nlp' model.
        doc1 = nlp(text1)
        doc2 = nlp(text2)
        
        return doc1.similarity(doc2)

    def _calculate_keyword_score(self, text1: str, text2: str) -> float:
        """
        Calculates the lexical overlap using Jaccard similarity.
        """
        # FIX: This also correctly uses the globally loaded 'nlp' model.
        doc1 = nlp(text1)
        doc2 = nlp(text2)

        lemmas1 = {token.lemma_.lower() for token in doc1 if not token.is_stop and not token.is_punct}
        lemmas2 = {token.lemma_.lower() for token in doc2 if not token.is_stop and not token.is_punct}

        intersection = lemmas1.intersection(lemmas2)
        union = lemmas1.union(lemmas2)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)

    def suggest_mappings(self, namaste_term: str, namaste_definition: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        The main method to generate mapping suggestions for a given NAMASTE term.
        """
        print(f"  -> Searching for ICD-11 candidates for '{namaste_term}'...")
        
        search_query = f"{namaste_term} {namaste_definition}"
        search_results = self.icd_client.search_conditions(search_query, limit=20)
        
        candidates = search_results.get("destinationEntities", [])
        if not candidates:
            print(f"  -> No initial candidates found for '{namaste_term}'.")
            return []

        scored_suggestions = []
        
        for candidate in candidates:
            icd_term = candidate.get("title", "").strip()
            icd_id = candidate.get("@id", "").split('/')[-1]

            if not icd_term or not icd_id:
                continue

            try:
                entity_details = self.icd_client.get_entity_details(icd_id)
                
                # The API response sometimes uses '@value', so this is a robust way to get the definition
                icd_definition = entity_details.get("definition", {}).get("@value", icd_term)

                icd_code = self.icd_client.get_entity_context(icd_id).get("code", "Err") 

            except Exception as e:
                print(f"  -> WARN: Could not fetch details for {icd_id}. Error: {e}")
                icd_definition = icd_term
                icd_code = "Error fetching"

            similarity_score = self._calculate_similarity_score(namaste_definition, icd_definition)
            keyword_score = self._calculate_keyword_score(namaste_definition, icd_definition)

            final_score = (similarity_score * self.similarity_weight) + \
                          (keyword_score * self.keyword_weight)

            scored_suggestions.append({
                "icd_code": icd_code,
                "icd_term": icd_term,
                "icd_definition": icd_definition,
                "score": final_score,
                "score_details": {
                    "similarity": similarity_score,
                    "keyword": keyword_score
                }
            })

        ranked_suggestions = sorted(scored_suggestions, key=lambda x: x['score'], reverse=True)

        return ranked_suggestions[:top_n]


