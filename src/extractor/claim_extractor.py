"""
Enhanced Financial Claim Extractor with robust heuristic, regex, and structured JSON parsing.
Extracts financial claims, infers DSL operations, and maps input variables.
"""
import re
import json
import uuid
from typing import Dict, List, Any, Optional

class ClaimExtractor:
    """Extractor for numerical financial claims from text and structured payloads."""
    
    def __init__(self):
        # Patterns for finding numerical amounts ($4.82B, 4.82 billion, $100M, 42.3%)
        self.amount_pattern = re.compile(
            r'\$\s*\d*(?:\.\d+)?\s*(?:[BMK]|billion|million|thousand)?|\b\d+(?:\.\d+)?\s*(?:[BMK]|billion|million|thousand)\b',
            re.IGNORECASE
        )
        self.percent_pattern = re.compile(r'\b\d+(?:\.\d+)?\s*%')
        self.keyword_pattern = re.compile(
            r'\b(revenue|margin|eps|growth|ratio|income|profit|loss|assets|liabilities|equity|sales|cogs|opex|ebit|ebitda|synergies|shares|debt|cagr)\b',
            re.IGNORECASE
        )

    def extract_claims(self, text: str, filing_cik: str, filing_period: str, form_type: str) -> List[Dict[str, Any]]:
        """Extract claims from the provided document text or JSON structure."""
        stripped = text.strip()
        
        # Check if text is valid JSON with explicit claim structure
        if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('[') and stripped.endswith(']')):
            try:
                parsed_json = json.loads(stripped)
                if isinstance(parsed_json, dict):
                    if "claims" in parsed_json and isinstance(parsed_json["claims"], list):
                        claims = []
                        for c in parsed_json["claims"]:
                            claims.append(self._normalize_claim_dict(c, filing_cik, filing_period, form_type))
                        return claims
                    elif "operation" in parsed_json:
                        return [self._normalize_claim_dict(parsed_json, filing_cik, filing_period, form_type)]
                elif isinstance(parsed_json, list):
                    return [self._normalize_claim_dict(c, filing_cik, filing_period, form_type) for c in parsed_json if isinstance(c, dict)]
            except Exception:
                pass

        # Fallback to regex & pattern-based NLP extraction
        claims = self._extract_with_patterns(text)
        for claim in claims:
            claim['source_ref'] = f'filing://{filing_cik}/{form_type}/{filing_period}'
            
        return claims

    def _normalize_claim_dict(self, c: Dict[str, Any], filing_cik: str, filing_period: str, form_type: str) -> Dict[str, Any]:
        """Normalize a structured dictionary claim."""
        cid = c.get("claim_id") or str(uuid.uuid4())
        claim_text = c.get("claim_text") or c.get("text") or f"Claim {c.get('operation', 'verification')}"
        claim_type = c.get("claim_type") or "computable"
        operation = c.get("operation") or "identity"
        
        inputs = c.get("inputs", [])
        if isinstance(inputs, dict):
            inputs = [{"name": k, "value": v, "unit": "USD"} for k, v in inputs.items()]
            
        output = c.get("output", {})
        if not isinstance(output, dict):
            output = {"value": float(output), "unit": "USD"}

        return {
            "claim_id": cid,
            "claim_text": claim_text,
            "claim_type": claim_type,
            "inputs": inputs,
            "operation": operation,
            "output": output,
            "source_ref": f'filing://{filing_cik}/{form_type}/{filing_period}'
        }

    def _extract_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Regex and heuristic based claim extraction."""
        claims = []
        sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
                
            has_amount = bool(self.amount_pattern.search(sentence))
            has_percent = bool(self.percent_pattern.search(sentence))
            has_keyword = bool(self.keyword_pattern.search(sentence))
            
            if has_keyword and (has_amount or has_percent):
                raw_amounts = self.amount_pattern.findall(sentence)
                # Filter out pure year tokens (e.g. 2024, 2025)
                amounts_found = []
                for a in raw_amounts:
                    clean_a = a.replace('$', '').strip()
                    if clean_a in {'2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027'}:
                        continue
                    if self._parse_number(a) is not None:
                        amounts_found.append(a)

                percents_found = self.percent_pattern.findall(sentence)
                
                output_val = None
                output_unit = "USD"
                
                # Check for percentage output
                if percents_found:
                    output_val = self._parse_number(percents_found[0])
                    output_unit = "percent"
                elif amounts_found:
                    output_val = self._parse_number(amounts_found[0])
                    output_unit = "USD"
                        
                claim_type = self._classify_claim(sentence)
                operation, extracted_inputs = self._infer_operation_and_inputs(sentence, amounts_found, percents_found)
                
                # If specific output was derived from operation, adjust
                if output_val is None and amounts_found:
                    output_val = self._parse_number(amounts_found[-1])
                
                claim_obj = {
                    'claim_id': str(uuid.uuid4()),
                    'claim_text': sentence,
                    'claim_type': claim_type,
                    'inputs': extracted_inputs,
                    'operation': operation,
                    'output': {'value': output_val, 'unit': output_unit} if output_val is not None else {'value': 0.0, 'unit': output_unit},
                }
                claims.append(claim_obj)
                
        return claims

    def _classify_claim(self, claim_text: str) -> str:
        """Classify a claim as computable or non-computable."""
        lower_text = claim_text.lower()
        non_computable_signals = [
            'estimate', 'project', 'forecast', 'expect', 'anticipate', 'synergies',
            'may', 'could', 'believe', 'guidance', 'target', 'outlook', 'undisclosed'
        ]
        if any(signal in lower_text for signal in non_computable_signals):
            return "non-computable"
        return "computable"

    def _infer_operation_and_inputs(self, claim_text: str, amounts: List[str], percents: List[str]) -> tuple[str, List[Dict[str, Any]]]:
        """Infer operation name matching SymbolicReExecutor DSL and parse named variables."""
        lower = claim_text.lower()
        inputs = []
        
        # 1. Operating Margin: (rev - cogs - opex) / rev
        if 'operating margin' in lower or ('margin' in lower and any(w in lower for w in ['opex', 'operating expense', 'operating expenses', 'operating income'])):
            rev_match = re.search(r'(?:revenue|sales|total revenue)s?\s*(?:of|was|totaled)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            cogs_match = re.search(r'(?:cost of revenue|cost of revenues|cost of goods|cogs)\s*(?:of|was|totaled)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            opex_match = re.search(r'(?:operating expense|operating expenses|opex)s?\s*(?:of|was|totaled)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            
            rev_val = self._parse_number(rev_match.group(1)) if rev_match and self._parse_number(rev_match.group(1)) else (self._parse_number(amounts[0]) if len(amounts) > 0 else None)
            cogs_val = self._parse_number(cogs_match.group(1)) if cogs_match and self._parse_number(cogs_match.group(1)) else (self._parse_number(amounts[1]) if len(amounts) > 1 else None)
            opex_val = self._parse_number(opex_match.group(1)) if opex_match and self._parse_number(opex_match.group(1)) else (self._parse_number(amounts[2]) if len(amounts) > 2 else None)
            
            if rev_val is not None: inputs.append({"name": "rev", "value": rev_val, "unit": "USD"})
            if cogs_val is not None: inputs.append({"name": "cogs", "value": cogs_val, "unit": "USD"})
            if opex_val is not None: inputs.append({"name": "opex", "value": opex_val, "unit": "USD"})
            return "operating_margin", inputs

        # 2. Gross Margin: (rev - cogs) / rev
        if 'gross margin' in lower or ('margin' in lower and any(w in lower for w in ['cogs', 'cost of goods', 'cost of revenue', 'cost of sales'])):
            rev_match = re.search(r'(?:revenue|sales|net revenue)s?\s*(?:of|was|reached|totaled)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million|thousand)?)', claim_text, re.IGNORECASE)
            cogs_match = re.search(r'(?:cost of goods sold|cogs|cost of revenue|cost of sales)s?\s*(?:of|was|totaled)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million|thousand)?)', claim_text, re.IGNORECASE)
            
            rev_val = self._parse_number(rev_match.group(1)) if rev_match and self._parse_number(rev_match.group(1)) else (self._parse_number(amounts[0]) if len(amounts) > 0 else None)
            cogs_val = self._parse_number(cogs_match.group(1)) if cogs_match and self._parse_number(cogs_match.group(1)) else (self._parse_number(amounts[1]) if len(amounts) > 1 else None)
            
            if rev_val is not None:
                inputs.append({"name": "rev", "value": rev_val, "unit": "USD"})
            if cogs_val is not None:
                inputs.append({"name": "cogs", "value": cogs_val, "unit": "USD"})
                
            return "gross_margin", inputs

        # 3. Net Margin: net_income / rev
        if 'net margin' in lower or 'profit margin' in lower or ('net income' in lower and 'revenue' in lower and 'margin' in lower):
            ni_match = re.search(r'(?:net income|net profit|earnings)\s*(?:of|was|reached)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            rev_match = re.search(r'(?:revenue|sales)\s*(?:of|was|totaled)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            
            ni_val = self._parse_number(ni_match.group(1)) if ni_match and self._parse_number(ni_match.group(1)) else (self._parse_number(amounts[0]) if len(amounts) > 0 else None)
            rev_val = self._parse_number(rev_match.group(1)) if rev_match and self._parse_number(rev_match.group(1)) else (self._parse_number(amounts[1]) if len(amounts) > 1 else None)
            
            if ni_val is not None: inputs.append({"name": "net_income", "value": ni_val, "unit": "USD"})
            if rev_val is not None: inputs.append({"name": "rev", "value": rev_val, "unit": "USD"})
            return "net_margin", inputs

        # 4. Diluted / Basic EPS: net_income / shares
        if 'diluted' in lower and ('eps' in lower or 'earnings per share' in lower):
            ni_match = re.search(r'(?:net income|net profit)\s*(?:of|was|reaching)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            shares_match = re.search(r'(\d+(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)\s*diluted\s+shares', claim_text, re.IGNORECASE)
            
            ni_val = self._parse_number(ni_match.group(1)) if ni_match and self._parse_number(ni_match.group(1)) else None
            if ni_val is None:
                for a in amounts:
                    v = self._parse_number(a)
                    if v and v > 1000:
                        ni_val = v
                        break
            
            shares_val = self._parse_number(shares_match.group(1)) if shares_match and self._parse_number(shares_match.group(1)) else (self._parse_number(amounts[-1]) if len(amounts) > 1 else None)
            
            if ni_val is not None: inputs.append({"name": "net_income", "value": ni_val, "unit": "USD"})
            if shares_val is not None: inputs.append({"name": "diluted_shares", "value": shares_val, "unit": "shares"})
            return "diluted_eps", inputs

        if 'eps' in lower or 'earnings per share' in lower:
            ni_match = re.search(r'(?:net income|net profit)\s*(?:of|was)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            shares_match = re.search(r'(\d+(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)\s*(?:basic\s+)?shares', claim_text, re.IGNORECASE)
            
            ni_val = self._parse_number(ni_match.group(1)) if ni_match and self._parse_number(ni_match.group(1)) else None
            if ni_val is None:
                for a in amounts:
                    v = self._parse_number(a)
                    if v and v > 1000:
                        ni_val = v
                        break
            shares_val = self._parse_number(shares_match.group(1)) if shares_match and self._parse_number(shares_match.group(1)) else (self._parse_number(amounts[-1]) if len(amounts) > 1 else None)
            
            if ni_val is not None: inputs.append({"name": "net_income", "value": ni_val, "unit": "USD"})
            if shares_val is not None: inputs.append({"name": "shares", "value": shares_val, "unit": "shares"})
            return "basic_eps", inputs

        # 5. P/E Ratio: price / eps
        if 'p/e' in lower or 'price to earnings' in lower:
            price_match = re.search(r'(?:price|stock price|trading at)\s*(?:of)?\s*(\$?\d+(?:\.\d+)?)', claim_text, re.IGNORECASE)
            eps_match = re.search(r'(?:eps|earnings per share)\s*(?:of)?\s*(\$?\d+(?:\.\d+)?)', claim_text, re.IGNORECASE)
            
            price_val = self._parse_number(price_match.group(1)) if price_match else (self._parse_number(amounts[0]) if len(amounts) > 0 else None)
            eps_val = self._parse_number(eps_match.group(1)) if eps_match else (self._parse_number(amounts[1]) if len(amounts) > 1 else None)
            
            if price_val is not None: inputs.append({"name": "price", "value": price_val, "unit": "USD"})
            if eps_val is not None: inputs.append({"name": "eps", "value": eps_val, "unit": "USD"})
            return "pe_ratio", inputs

        # 6. Debt to Equity: total_debt / total_equity
        if 'debt to equity' in lower or 'debt-to-equity' in lower or 'd/e' in lower:
            debt_match = re.search(r'(?:debt|total debt)\s*(?:of|was)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            equity_match = re.search(r'(?:equity|total equity|stockholders equity)\s*(?:of|was)?\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?)', claim_text, re.IGNORECASE)
            
            debt_val = self._parse_number(debt_match.group(1)) if debt_match and self._parse_number(debt_match.group(1)) else (self._parse_number(amounts[0]) if len(amounts) > 0 else None)
            equity_val = self._parse_number(equity_match.group(1)) if equity_match and self._parse_number(equity_match.group(1)) else (self._parse_number(amounts[1]) if len(amounts) > 1 else None)
            
            if debt_val is not None: inputs.append({"name": "total_debt", "value": debt_val, "unit": "USD"})
            if equity_val is not None: inputs.append({"name": "total_equity", "value": equity_val, "unit": "USD"})
            return "debt_to_equity", inputs

        # 7. YoY Change: (new - old) / old
        if 'yoy' in lower or 'year-over-year' in lower or 'grew' in lower or 'increased by' in lower or 'growth' in lower:
            old_match = re.search(r'(?:from|up from|compared to)\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?%?)', claim_text, re.IGNORECASE)
            new_match = re.search(r'(?:to|reached|was|reported)\s*(\$?\d*(?:\.\d+)?\s*(?:[bmkBMK]|billion|million)?%?)', claim_text, re.IGNORECASE)
            
            old_val = self._parse_number(old_match.group(1)) if old_match and self._parse_number(old_match.group(1)) else (self._parse_number(amounts[1]) if len(amounts) > 1 else None)
            new_val = self._parse_number(new_match.group(1)) if new_match and self._parse_number(new_match.group(1)) else (self._parse_number(amounts[0]) if len(amounts) > 0 else None)
            
            if old_val is not None: inputs.append({"name": "old", "value": old_val, "unit": "USD"})
            if new_val is not None: inputs.append({"name": "new", "value": new_val, "unit": "USD"})
            return "yoy_change", inputs

        # Default fallback
        if len(amounts) >= 2:
            val_a = self._parse_number(amounts[0])
            val_b = self._parse_number(amounts[1])
            if val_a is not None and val_b is not None:
                inputs = [{"name": "a", "value": val_a, "unit": "USD"}, {"name": "b", "value": val_b, "unit": "USD"}]
                return "addition", inputs

        return "identity", inputs

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse various number formats to standard float."""
        if not text:
            return None
        clean_text = text.replace('$', '').replace(',', '').strip().lower()
        
        multiplier = 1.0
        if 'b' in clean_text or 'billion' in clean_text:
            multiplier = 1_000_000_000.0
            clean_text = clean_text.replace('billion', '').replace('b', '').strip()
        elif 'm' in clean_text or 'million' in clean_text:
            multiplier = 1_000_000.0
            clean_text = clean_text.replace('million', '').replace('m', '').strip()
        elif 'k' in clean_text or 'thousand' in clean_text:
            multiplier = 1_000.0
            clean_text = clean_text.replace('thousand', '').replace('k', '').strip()
        elif '%' in clean_text:
            multiplier = 0.01
            clean_text = clean_text.replace('%', '').strip()
            
        try:
            return float(clean_text) * multiplier
        except ValueError:
            return None
