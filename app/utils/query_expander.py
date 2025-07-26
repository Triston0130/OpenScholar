"""
Advanced Query Understanding and Expansion
Implements sophisticated query analysis with entity recognition and semantic expansion
"""

import re
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Advanced query expansion with domain-specific knowledge
    """
    
    def __init__(self):
        self._initialize_knowledge_bases()
    
    def _initialize_knowledge_bases(self):
        """Initialize domain-specific knowledge bases"""
        
        # Academic abbreviation expansions
        self.abbreviations = {
            # Computer Science
            'ml': ['machine learning'],
            'ai': ['artificial intelligence'],
            'nn': ['neural network', 'neural networks'],
            'cnn': ['convolutional neural network', 'convolutional neural networks'],
            'rnn': ['recurrent neural network', 'recurrent neural networks'],
            'lstm': ['long short-term memory', 'long short term memory'],
            'gan': ['generative adversarial network', 'generative adversarial networks'],
            'nlp': ['natural language processing'],
            'cv': ['computer vision'],
            'rl': ['reinforcement learning'],
            'dl': ['deep learning'],
            'hci': ['human computer interaction', 'human-computer interaction'],
            'ux': ['user experience'],
            'ui': ['user interface'],
            'api': ['application programming interface'],
            'sql': ['structured query language'],
            'nosql': ['non-relational database', 'not only sql'],
            'iot': ['internet of things'],
            'aws': ['amazon web services'],
            'gcp': ['google cloud platform'],
            'k8s': ['kubernetes'],
            'ci/cd': ['continuous integration', 'continuous deployment'],
            'devops': ['development operations'],
            'os': ['operating system', 'operating systems'],
            'db': ['database', 'databases'],
            'gpu': ['graphics processing unit'],
            'cpu': ['central processing unit'],
            'ram': ['random access memory'],
            'svm': ['support vector machine', 'support vector machines'],
            'knn': ['k-nearest neighbors', 'k nearest neighbors'],
            'rf': ['random forest'],
            'xgb': ['extreme gradient boosting', 'xgboost'],
            'bert': ['bidirectional encoder representations from transformers'],
            'gpt': ['generative pretrained transformer', 'generative pre-trained transformer'],
            
            # Medical/Biology
            'covid': ['covid-19', 'coronavirus disease 2019', 'sars-cov-2'],
            'sars': ['severe acute respiratory syndrome'],
            'mers': ['middle east respiratory syndrome'],
            'hiv': ['human immunodeficiency virus'],
            'aids': ['acquired immunodeficiency syndrome'],
            'dna': ['deoxyribonucleic acid'],
            'rna': ['ribonucleic acid'],
            'mrna': ['messenger rna', 'messenger ribonucleic acid'],
            'pcr': ['polymerase chain reaction'],
            'ct': ['computed tomography', 'ct scan'],
            'mri': ['magnetic resonance imaging'],
            'ecg': ['electrocardiogram', 'ekg'],
            'eeg': ['electroencephalogram'],
            'icu': ['intensive care unit'],
            'er': ['emergency room', 'emergency department'],
            'bp': ['blood pressure'],
            'hr': ['heart rate'],
            'bmi': ['body mass index'],
            'copd': ['chronic obstructive pulmonary disease'],
            'ckd': ['chronic kidney disease'],
            'cad': ['coronary artery disease'],
            'chf': ['congestive heart failure'],
            'dm': ['diabetes mellitus'],
            't2d': ['type 2 diabetes', 'type 2 diabetes mellitus'],
            't1d': ['type 1 diabetes', 'type 1 diabetes mellitus'],
            
            # General Academic
            'phd': ['doctor of philosophy', 'doctoral'],
            'ma': ['master of arts'],
            'ms': ['master of science'],
            'bs': ['bachelor of science'],
            'ba': ['bachelor of arts'],
            'rct': ['randomized controlled trial', 'randomised controlled trial'],
            'doi': ['digital object identifier'],
            'isbn': ['international standard book number'],
            'issn': ['international standard serial number'],
            'if': ['impact factor'],
            'h-index': ['hirsch index'],
            'oa': ['open access'],
            'cc': ['creative commons'],
            'usa': ['united states', 'united states of america'],
            'uk': ['united kingdom', 'britain'],
            'eu': ['european union'],
            'who': ['world health organization'],
            'cdc': ['centers for disease control', 'centers for disease control and prevention'],
            'nih': ['national institutes of health'],
            'nsf': ['national science foundation'],
            'nasa': ['national aeronautics and space administration'],
            'ieee': ['institute of electrical and electronics engineers'],
            'acm': ['association for computing machinery'],
            'aaai': ['association for the advancement of artificial intelligence'],
        }
        
        # Synonym mappings
        self.synonyms = {
            # Computer Science
            'algorithm': ['method', 'approach', 'technique', 'procedure'],
            'neural network': ['deep learning', 'artificial neural network', 'ann'],
            'machine learning': ['ml', 'statistical learning', 'pattern recognition'],
            'artificial intelligence': ['ai', 'intelligent systems', 'computational intelligence'],
            'database': ['data store', 'data repository', 'dbms'],
            'software': ['application', 'program', 'system'],
            'optimization': ['optimisation', 'improvement', 'enhancement'],
            'classification': ['categorization', 'labeling', 'sorting'],
            'prediction': ['forecasting', 'estimation', 'projection'],
            'analysis': ['examination', 'study', 'investigation'],
            'evaluation': ['assessment', 'validation', 'testing'],
            'performance': ['efficiency', 'speed', 'effectiveness'],
            'accuracy': ['precision', 'correctness', 'exactness'],
            'error': ['mistake', 'fault', 'bug', 'defect'],
            'framework': ['platform', 'architecture', 'system'],
            'model': ['algorithm', 'method', 'approach'],
            'data': ['information', 'dataset', 'records'],
            'visualization': ['visualisation', 'display', 'representation'],
            'security': ['safety', 'protection', 'privacy'],
            'network': ['graph', 'topology', 'connection'],
            
            # Medical/Biology
            'disease': ['illness', 'disorder', 'condition', 'pathology'],
            'treatment': ['therapy', 'intervention', 'management'],
            'patient': ['subject', 'participant', 'individual'],
            'diagnosis': ['detection', 'identification', 'assessment'],
            'symptom': ['sign', 'manifestation', 'presentation'],
            'cancer': ['tumor', 'tumour', 'malignancy', 'neoplasm', 'carcinoma'],
            'infection': ['contagion', 'contamination', 'sepsis'],
            'vaccine': ['vaccination', 'immunization', 'inoculation'],
            'drug': ['medication', 'medicine', 'pharmaceutical', 'compound'],
            'clinical': ['medical', 'therapeutic', 'healthcare'],
            'trial': ['study', 'experiment', 'investigation'],
            'outcome': ['result', 'endpoint', 'effect'],
            'risk': ['hazard', 'danger', 'probability'],
            'prevention': ['prophylaxis', 'protection', 'avoidance'],
            'screening': ['detection', 'testing', 'examination'],
            'biomarker': ['marker', 'indicator', 'measure'],
            'gene': ['genetic', 'genomic', 'hereditary'],
            'protein': ['peptide', 'polypeptide', 'enzyme'],
            'cell': ['cellular', 'cytological'],
            'tissue': ['organ', 'biological material'],
            
            # General Academic
            'research': ['study', 'investigation', 'inquiry', 'exploration'],
            'review': ['survey', 'overview', 'meta-analysis', 'systematic review'],
            'method': ['methodology', 'approach', 'technique', 'procedure'],
            'result': ['finding', 'outcome', 'conclusion'],
            'significant': ['important', 'meaningful', 'substantial'],
            'novel': ['new', 'innovative', 'original', 'unique'],
            'effective': ['efficient', 'successful', 'beneficial'],
            'challenge': ['problem', 'issue', 'difficulty', 'obstacle'],
            'solution': ['answer', 'resolution', 'remedy'],
            'application': ['use', 'implementation', 'deployment'],
            'comparison': ['contrast', 'evaluation', 'benchmarking'],
            'improvement': ['enhancement', 'advancement', 'progress'],
            'limitation': ['constraint', 'restriction', 'drawback'],
            'future': ['prospective', 'upcoming', 'emerging'],
            'recent': ['current', 'contemporary', 'latest', 'new'],
        }
        
        # Related concept mappings
        self.related_concepts = {
            # ML/AI concepts
            'deep learning': ['neural networks', 'backpropagation', 'gradient descent', 'tensorflow', 'pytorch'],
            'computer vision': ['image processing', 'object detection', 'image classification', 'opencv', 'yolo'],
            'natural language processing': ['text mining', 'sentiment analysis', 'named entity recognition', 'bert', 'transformers'],
            'reinforcement learning': ['q-learning', 'policy gradient', 'markov decision process', 'reward function'],
            'supervised learning': ['classification', 'regression', 'labeled data', 'training set'],
            'unsupervised learning': ['clustering', 'dimensionality reduction', 'anomaly detection', 'pca', 'autoencoder'],
            
            # Medical concepts
            'covid-19': ['pandemic', 'vaccination', 'spike protein', 'variants', 'transmission'],
            'cancer treatment': ['chemotherapy', 'radiation', 'immunotherapy', 'targeted therapy', 'surgery'],
            'diabetes': ['insulin', 'glucose', 'blood sugar', 'complications', 'management'],
            'cardiovascular': ['heart disease', 'stroke', 'hypertension', 'atherosclerosis', 'cardiac'],
            'mental health': ['depression', 'anxiety', 'psychiatry', 'therapy', 'psychological'],
            
            # Research methods
            'systematic review': ['meta-analysis', 'literature review', 'prisma', 'cochrane'],
            'randomized controlled trial': ['clinical trial', 'intervention', 'control group', 'blinding'],
            'machine learning evaluation': ['cross-validation', 'metrics', 'overfitting', 'generalization'],
        }
        
        # Domain-specific query templates
        self.query_patterns = {
            'comparison': r'(.*?)\s+(?:vs\.?|versus|compared to|vs|compare)\s+(.*)',
            'review': r'(?:systematic\s+)?review\s+(?:of\s+)?(.*)',
            'tutorial': r'(?:how\s+to|tutorial|guide|introduction\s+to)\s+(.*)',
            'implementation': r'(?:implement|implementing|implementation\s+of)\s+(.*)',
            'evaluation': r'(?:evaluate|evaluating|evaluation\s+of|assessment\s+of)\s+(.*)',
            'application': r'(.*?)\s+(?:for|in|applied to)\s+(.*)',
        }
    
    def expand_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive query expansion
        
        Returns:
            Dictionary containing:
            - original_query: The original query
            - expanded_queries: List of expanded query variations
            - entities: Detected entities in the query
            - concepts: Related concepts
            - query_type: Type of query (comparison, review, etc.)
            - suggestions: Query suggestions
        """
        result = {
            'original_query': query,
            'expanded_queries': [],
            'entities': {},
            'concepts': [],
            'query_type': 'general',
            'suggestions': []
        }
        
        # Clean and normalize query
        normalized_query = self._normalize_query(query)
        
        # Detect query type
        query_type = self._detect_query_type(normalized_query)
        result['query_type'] = query_type
        
        # Extract entities
        entities = self._extract_entities(normalized_query)
        result['entities'] = entities
        
        # Expand abbreviations
        expanded_abbrev = self._expand_abbreviations(normalized_query)
        if expanded_abbrev != normalized_query:
            result['expanded_queries'].append(expanded_abbrev)
        
        # Add synonyms
        synonym_queries = self._generate_synonym_queries(normalized_query)
        result['expanded_queries'].extend(synonym_queries[:3])  # Limit to top 3
        
        # Add related concepts
        concepts = self._find_related_concepts(normalized_query)
        result['concepts'] = concepts[:5]  # Limit to top 5
        
        # Generate query suggestions based on type
        suggestions = self._generate_suggestions(normalized_query, query_type, context)
        result['suggestions'] = suggestions
        
        # Domain-specific expansions
        if context and context.get('discipline'):
            domain_expansions = self._domain_specific_expansion(normalized_query, context['discipline'])
            result['expanded_queries'].extend(domain_expansions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_expansions = []
        for q in result['expanded_queries']:
            if q not in seen and q != normalized_query:
                seen.add(q)
                unique_expansions.append(q)
        result['expanded_queries'] = unique_expansions[:5]  # Limit total expansions
        
        return result
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for processing"""
        # Convert to lowercase
        query = query.lower()
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        # Remove extra punctuation but keep meaningful ones
        query = re.sub(r'[^\w\s\-\./:]', ' ', query)
        query = ' '.join(query.split())
        
        return query
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query"""
        for query_type, pattern in self.query_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return query_type
        
        # Additional heuristics
        if 'review' in query or 'survey' in query:
            return 'review'
        elif 'how' in query or 'tutorial' in query:
            return 'tutorial'
        elif any(word in query for word in ['implement', 'build', 'create', 'develop']):
            return 'implementation'
        elif any(word in query for word in ['evaluate', 'compare', 'benchmark', 'test']):
            return 'evaluation'
        elif any(word in query for word in ['apply', 'application', 'use case']):
            return 'application'
        
        return 'general'
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from query"""
        entities = {
            'abbreviations': [],
            'years': [],
            'authors': [],
            'techniques': [],
            'domains': []
        }
        
        # Extract abbreviations
        for abbrev in self.abbreviations:
            if re.search(r'\b' + re.escape(abbrev) + r'\b', query, re.IGNORECASE):
                entities['abbreviations'].append(abbrev)
        
        # Extract years
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', query)
        entities['years'] = years
        
        # Extract potential author names (Last, F. or F. Last patterns)
        author_patterns = [
            r'[A-Z][a-z]+,\s*[A-Z]\.',  # Smith, J.
            r'[A-Z]\.\s*[A-Z][a-z]+',   # J. Smith
            r'[A-Z][a-z]+\s+et\s+al\.?' # Smith et al
        ]
        for pattern in author_patterns:
            authors = re.findall(pattern, query)
            entities['authors'].extend(authors)
        
        # Extract known techniques/methods
        known_techniques = [
            'machine learning', 'deep learning', 'neural network',
            'random forest', 'svm', 'gradient boosting',
            'clustering', 'classification', 'regression'
        ]
        for technique in known_techniques:
            if technique in query.lower():
                entities['techniques'].append(technique)
        
        return entities
    
    def _expand_abbreviations(self, query: str) -> str:
        """Expand abbreviations in query"""
        expanded = query
        
        for abbrev, expansions in self.abbreviations.items():
            # Case-insensitive word boundary match
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, expanded, re.IGNORECASE):
                # Use the first expansion
                expanded = re.sub(pattern, expansions[0], expanded, flags=re.IGNORECASE)
        
        return expanded
    
    def _generate_synonym_queries(self, query: str) -> List[str]:
        """Generate queries with synonyms"""
        variations = []
        words = query.split()
        
        # For each word, check if we have synonyms
        for i, word in enumerate(words):
            if word in self.synonyms:
                # Create variations with each synonym
                for synonym in self.synonyms[word][:2]:  # Limit synonyms per word
                    new_words = words[:i] + [synonym] + words[i+1:]
                    variations.append(' '.join(new_words))
        
        # Also check for multi-word phrases
        for phrase, synonyms in self.synonyms.items():
            if ' ' in phrase and phrase in query:
                for synonym in synonyms[:2]:
                    variations.append(query.replace(phrase, synonym))
        
        return variations
    
    def _find_related_concepts(self, query: str) -> List[str]:
        """Find related concepts for the query"""
        concepts = []
        
        # Check each concept mapping
        for concept, related in self.related_concepts.items():
            if concept.lower() in query.lower():
                concepts.extend(related)
        
        # Also check individual words
        words = query.lower().split()
        for word in words:
            if word in self.related_concepts:
                concepts.extend(self.related_concepts[word])
        
        # Remove duplicates and return
        return list(set(concepts))
    
    def _generate_suggestions(self, query: str, query_type: str, context: Dict[str, Any]) -> List[str]:
        """Generate query suggestions based on type and context"""
        suggestions = []
        
        if query_type == 'review':
            suggestions.extend([
                f"{query} systematic review",
                f"{query} meta-analysis",
                f"{query} literature survey"
            ])
        elif query_type == 'comparison':
            # Extract what's being compared
            match = re.search(self.query_patterns['comparison'], query)
            if match:
                item1, item2 = match.groups()
                suggestions.extend([
                    f"{item1} vs {item2} performance comparison",
                    f"{item1} versus {item2} empirical evaluation",
                    f"comparative analysis {item1} {item2}"
                ])
        elif query_type == 'tutorial':
            suggestions.extend([
                f"{query} step by step",
                f"{query} beginner guide",
                f"{query} implementation example"
            ])
        elif query_type == 'implementation':
            suggestions.extend([
                f"{query} source code",
                f"{query} github implementation",
                f"{query} algorithm pseudocode"
            ])
        
        # Add temporal suggestions if no year specified
        if not re.search(r'\b(19\d{2}|20\d{2})\b', query):
            current_year = 2024
            suggestions.append(f"{query} {current_year}")
            suggestions.append(f"{query} recent advances")
        
        return suggestions[:5]  # Limit suggestions
    
    def _domain_specific_expansion(self, query: str, discipline: str) -> List[str]:
        """Generate domain-specific query expansions"""
        expansions = []
        
        discipline_lower = discipline.lower()
        
        if 'computer' in discipline_lower or 'cs' in discipline_lower:
            # Add CS-specific terms
            if 'algorithm' not in query:
                expansions.append(f"{query} algorithm")
            if 'implementation' not in query and 'implement' not in query:
                expansions.append(f"{query} implementation")
            
        elif 'medic' in discipline_lower or 'health' in discipline_lower:
            # Add medical-specific terms
            if 'clinical' not in query:
                expansions.append(f"{query} clinical")
            if 'patient' not in query:
                expansions.append(f"{query} patient outcomes")
                
        elif 'bio' in discipline_lower:
            # Add biology-specific terms
            if 'molecular' not in query:
                expansions.append(f"{query} molecular")
            if 'cell' not in query:
                expansions.append(f"{query} cellular")
        
        return expansions
    
    def get_query_statistics(self, query: str) -> Dict[str, Any]:
        """Get statistics about a query"""
        words = query.lower().split()
        
        stats = {
            'length': len(words),
            'has_abbreviations': any(word in self.abbreviations for word in words),
            'has_year': bool(re.search(r'\b(19\d{2}|20\d{2})\b', query)),
            'has_quotes': '"' in query,
            'has_boolean': any(op in query.upper() for op in ['AND', 'OR', 'NOT']),
            'complexity': 'simple' if len(words) <= 3 else 'moderate' if len(words) <= 6 else 'complex'
        }
        
        return stats