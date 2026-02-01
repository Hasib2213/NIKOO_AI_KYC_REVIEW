"""
Content Co-pilot Router
Provides content validation, improvement suggestions, and pre-publish checks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
from app.LLM_Service.ai_service import groq_service
from app.services.rag_service import rag_service
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/content", tags=["Content Co-pilot"])


class ContentCheckRequest(BaseModel):
    user_id: str
    content: str = Field(..., description="Content to check (post description, listing, etc.)")
    content_type: str = Field(default="post", description="Type: post, marketplace_listing, comment")
    

class ContentCheckResponse(BaseModel):
    safe: bool
    issues: List[str] = []
    suggestions: List[str] = []
    improved_content: Optional[str] = None
    risk_score: float = Field(ge=0, le=1, description="0 = safe, 1 = high risk")
    

class ContentImproveRequest(BaseModel):
    user_id: str
    content: str
    improvement_type: str = Field(
        default="grammar",
        description="Type: grammar, clarity, marketplace_optimize, engagement"
    )


class ContentImproveResponse(BaseModel):
    original: str
    improved: str
    changes_made: List[str]
    

@router.post("/check", response_model=ContentCheckResponse)
async def check_content(request: ContentCheckRequest):
    """
    Pre-publish content check for safety, policy violations, and quality
    """
    try:
        logger.info(f"Checking content for user {request.user_id}, type: {request.content_type}")
        
        # Get policy context from RAG if available
        policy_context = ""
        if rag_service.is_initialized:
            policy_context = await rag_service.get_relevant_context_string(
                f"content policy {request.content_type} forbidden",
                k=2
            )
        
        # Build analysis prompt
        analysis_prompt = f"""Analyze this {request.content_type} content for safety and policy compliance:

Content: "{request.content}"

{policy_context}

Check for:
1. Forbidden content (violence, hate speech, adult content, illegal items)
2. Scam indicators (too good to be true, urgent pressure, suspicious links)
3. Policy violations (spam, misleading claims, impersonation)
4. Quality issues (poor grammar, unclear message, missing details)

Respond in JSON format:
{{
    "safe": true/false,
    "risk_score": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        messages = [{"role": "user", "content": analysis_prompt}]
        
        response = await groq_service.generate_response(messages, request.user_id)
        
        # Parse response
        import json
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # Generate improved version if issues found
            improved = None
            if result.get("issues") and result.get("suggestions"):
                improved = await _improve_content(request.content, result["suggestions"])
            
            return ContentCheckResponse(
                safe=result.get("safe", True),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                improved_content=improved,
                risk_score=result.get("risk_score", 0.0)
            )
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response}")
            # Fallback: basic analysis
            return ContentCheckResponse(
                safe=True,
                issues=[],
                suggestions=["Unable to perform detailed analysis"],
                risk_score=0.0
            )
        
    except Exception as e:
        logger.error(f"Error checking content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/improve", response_model=ContentImproveResponse)
async def improve_content(request: ContentImproveRequest):
    """
    Improve content quality (grammar, clarity, engagement)
    """
    try:
        logger.info(f"Improving content for user {request.user_id}, type: {request.improvement_type}")
        
        improvement_prompts = {
            "grammar": "Fix grammar and spelling errors while preserving the original meaning and tone.",
            "clarity": "Make the message clearer and more concise while keeping all important information.",
            "marketplace_optimize": "Optimize for marketplace listing: clear title, compelling description, key features, and call-to-action.",
            "engagement": "Make the content more engaging and appealing while staying authentic."
        }
        
        prompt_instruction = improvement_prompts.get(
            request.improvement_type,
            improvement_prompts["grammar"]
        )
        
        improve_prompt = f"""Improve this content:

Original: "{request.content}"

Task: {prompt_instruction}

Respond in JSON format:
{{
    "improved": "improved content here",
    "changes_made": ["change1", "change2"]
}}

Keep the same language as the original. Do not change the core message."""

        messages = [{"role": "user", "content": improve_prompt}]
        
        response = await groq_service.generate_response(messages, request.user_id)
        
        # Parse response
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            return ContentImproveResponse(
                original=request.content,
                improved=result.get("improved", request.content),
                changes_made=result.get("changes_made", [])
            )
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse improvement response: {response}")
            return ContentImproveResponse(
                original=request.content,
                improved=request.content,
                changes_made=["Unable to generate improvements"]
            )
        
    except Exception as e:
        logger.error(f"Error improving content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _improve_content(content: str, suggestions: List[str]) -> str:
    """Helper to improve content based on suggestions"""
    try:
        prompt = f"""Improve this content based on the suggestions:

Content: "{content}"

Suggestions:
{chr(10).join(f'- {s}' for s in suggestions)}

Provide only the improved version, no explanations."""

        messages = [{"role": "user", "content": prompt}]
        improved = await groq_service.generate_response(messages, "system")
        return improved.strip('"').strip()
        
    except Exception as e:
        logger.error(f"Error in auto-improvement: {e}")
        return content


@router.post("/validate-marketplace")
async def validate_marketplace_listing(request: ContentCheckRequest):
    """
    Validate marketplace listing completeness and quality
    """
    try:
        validation_prompt = f"""Validate this marketplace listing:

"{request.content}"

Check for:
1. Clear product/service name
2. Price mentioned or indicated
3. Condition/quality described
4. Key details included
5. No prohibited items (weapons, drugs, counterfeit, etc.)
6. Professional and trustworthy tone

Respond in JSON:
{{
    "valid": true/false,
    "completeness_score": 0-100,
    "missing_elements": ["element1"],
    "warnings": ["warning1"],
    "suggestions": ["suggestion1"]
}}"""

        messages = [{"role": "user", "content": validation_prompt}]
        response = await groq_service.generate_response(messages, request.user_id)
        
        import json
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        else:
            json_str = response.strip()
        
        result = json.loads(json_str)
        return result
        
    except Exception as e:
        logger.error(f"Error validating marketplace listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
