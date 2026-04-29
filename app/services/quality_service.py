from app.core.logger import get_logger

logger = get_logger("QualityGuard")

class QualityGuard:
    """
    Evaluates the quality of AI-generated responses based on 
    Walter Ambriz's business rules and style guidelines.
    """
    
    @staticmethod
    def evaluate(query: str, response: str) -> dict:
        """
        Runs quality checks on a response.
        
        Args:
            query (str): The original user query.
            response (str): The generated AI response.
            
        Returns:
            dict: Evaluation results containing score and flags.
        """
        score = 100
        flags = []
        
        # 1. Conciseness Validation (Maximum 5 lines of real content)
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if len(lines) > 5:
            score -= 30
            flags.append("TOO_LONG")
            
        # 2. Identity Validation (Avoid generic AI assistant sounding phrases)
        generic_phrases = [
            "as an ai language model",
            "as a large language model",
            "como modelo de lenguaje", 
            "claro que sí", 
            "estoy aquí para ayudarte",
            "en qué puedo ayudarte hoy"
        ]
        if any(phrase in response.lower() for phrase in generic_phrases):
            score -= 40
            flags.append("GENERIC_TONE")
            
        # 3. Persona Validation (Must mention or act as WALTER_AI)
        # If the response is long and lacks technical touch
        if score < 100 and "WALTER_AI" not in response.upper() and len(response) > 100:
            score -= 10
            flags.append("LOSS_OF_IDENTITY")

        # Log assessment result with professional status tags
        status = "PASSED" if score >= 80 else "WARNING" if score >= 50 else "FAILED"
        logger.info(f"Quality Assessment: [{status}] | Score: {score}/100 | Flags: {flags}")
        
        return {"score": score, "flags": flags}
