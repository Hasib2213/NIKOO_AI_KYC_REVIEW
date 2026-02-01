"""
Onboarding Helper Router
Provides step-by-step guidance for app features and common tasks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
from app.LLM_Service.ai_service import groq_service
from app.services.rag_service import rag_service
from app.services.permission_service import permission_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


class OnboardingRequest(BaseModel):
    user_id: str
    topic: str = Field(
        ...,
        description="Topic: kyc, wallet, marketplace, cap, streaming, profile, general"
    )
    question: Optional[str] = Field(None, description="Specific question about the topic")
    

class OnboardingStep(BaseModel):
    step_number: int
    title: str
    description: str
    tips: Optional[List[str]] = []
    

class OnboardingResponse(BaseModel):
    topic: str
    overview: str
    steps: List[OnboardingStep]
    helpful_links: Optional[List[str]] = []
    next_topic: Optional[str] = None
    

class QuickHelpRequest(BaseModel):
    user_id: str
    query: str
    

class QuickHelpResponse(BaseModel):
    answer: str
    related_topics: List[str] = []
    

# Predefined onboarding guides
ONBOARDING_GUIDES = {
    "kyc": {
        "title": "KYC Verification",
        "overview": "Complete KYC verification to unlock full app features including wallet withdrawals and marketplace selling.",
        "steps": [
            {
                "step_number": 1,
                "title": "Start Verification",
                "description": "Go to Profile → Settings → Verify Identity",
                "tips": ["Have your ID ready (passport, driver's license, or national ID)", "Ensure good lighting"]
            },
            {
                "step_number": 2,
                "title": "Submit Documents",
                "description": "Upload clear photos of your ID (front and back if applicable)",
                "tips": ["No glare or shadows", "All text must be readable", "ID must be valid"]
            },
            {
                "step_number": 3,
                "title": "Take Selfie",
                "description": "Take a live selfie for verification",
                "tips": ["Remove glasses and hat", "Good lighting on your face", "Look directly at camera"]
            },
            {
                "step_number": 4,
                "title": "Wait for Review",
                "description": "Your documents will be reviewed within 24-48 hours",
                "tips": ["Check notifications for updates", "You can track status in Profile"]
            }
        ],
        "next_topic": "wallet"
    },
    "wallet": {
        "title": "Wallet Setup & Usage",
        "overview": "Your in-app wallet lets you add credits, send tips, and receive payments.",
        "steps": [
            {
                "step_number": 1,
                "title": "Add Credits",
                "description": "Tap Wallet → + Add Credits → Choose amount → Pay with card",
                "tips": ["Credits added instantly", "Amounts: $10, $25, $50, $100, $250, $500, or custom"]
            },
            {
                "step_number": 2,
                "title": "Send Tips/Money",
                "description": "In any chat or profile → Send Money → Enter username and amount",
                "tips": ["Add optional message", "Transaction is instant", "Both users get notification"]
            },
            {
                "step_number": 3,
                "title": "Request Payout",
                "description": "Wallet → Request Payout → Enter amount (min $10) → Choose transfer method",
                "tips": ["KYC must be verified", "Bank Transfer: free, 3-5 days", "Instant: 1.5% fee"]
            }
        ],
        "next_topic": "marketplace"
    },
    "marketplace": {
        "title": "Buy & Sell Safely",
        "overview": "Marketplace with escrow protection ensures safe transactions for buyers and sellers.",
        "steps": [
            {
                "step_number": 1,
                "title": "Browse Listings",
                "description": "Go to Marketplace → Search or browse categories",
                "tips": ["Check seller reviews", "Read full description", "Look at all photos"]
            },
            {
                "step_number": 2,
                "title": "Make Purchase (Buyer)",
                "description": "Tap Buy Now → Enter card details → Payment held in Escrow",
                "tips": ["Money protected until delivery confirmed", "Seller ships after payment"]
            },
            {
                "step_number": 3,
                "title": "Confirm Delivery",
                "description": "Receive item → Order → Delivery Proof → Upload photos → Confirm Receipt",
                "tips": ["Take photos of packaging", "48 hours to confirm or dispute", "Funds released after confirmation"]
            },
            {
                "step_number": 4,
                "title": "Create Listing (Seller)",
                "description": "Marketplace → + New Listing → Add photos, description, price → Publish",
                "tips": ["Clear photos from multiple angles", "Honest description", "Competitive pricing"]
            }
        ],
        "next_topic": "cap"
    },
    "cap": {
        "title": "CAP - Capture Evidence",
        "overview": "Record verified photos/videos with metadata (GPS, timestamp, dual camera) for authenticity.",
        "steps": [
            {
                "step_number": 1,
                "title": "Wait for System Ready",
                "description": "App checks GPS, Network, IMU Sensors, Dual Camera - wait for all green ticks",
                "tips": ["Enable location services", "Ensure internet connection"]
            },
            {
                "step_number": 2,
                "title": "Start Capture",
                "description": "Tap 'All systems ready' → Start Capture → Camera opens",
                "tips": ["Switch to Dual Camera for PIP or Split view", "Adjust settings if needed"]
            },
            {
                "step_number": 3,
                "title": "Record Evidence",
                "description": "Tap red button → Record photo/video → Stop when done",
                "tips": ["Use both cameras for better proof", "Capture all relevant angles"]
            },
            {
                "step_number": 4,
                "title": "Review & Upload",
                "description": "Preview → Check metadata → Confirm → Add caption/tags → Upload",
                "tips": ["Verify GPS location is correct", "Add descriptive caption", "Choose audience visibility"]
            }
        ],
        "next_topic": "streaming"
    },
    "streaming": {
        "title": "Live Streaming",
        "overview": "Go live to interact with viewers in real-time and receive tips.",
        "steps": [
            {
                "step_number": 1,
                "title": "Start Stream",
                "description": "Tap + → Go Live → Add title and description",
                "tips": ["Choose interesting title", "Pick category", "Check camera/mic"]
            },
            {
                "step_number": 2,
                "title": "Interact with Viewers",
                "description": "Chat with viewers, respond to comments, acknowledge tips",
                "tips": ["Engage actively", "Thank tippers by name", "Keep content appropriate"]
            },
            {
                "step_number": 3,
                "title": "End Stream",
                "description": "Tap End Stream → Confirm → View statistics",
                "tips": ["Thank viewers before ending", "Check earnings", "Stream saved if public"]
            }
        ],
        "next_topic": "profile"
    },
    "profile": {
        "title": "Profile & Settings",
        "overview": "Customize your profile, manage privacy, and secure your account.",
        "steps": [
            {
                "step_number": 1,
                "title": "Edit Profile",
                "description": "Profile → Edit → Change avatar, name, username, bio",
                "tips": ["Choose clear profile photo", "Write engaging bio", "Username can be changed"]
            },
            {
                "step_number": 2,
                "title": "Privacy Settings",
                "description": "Settings → Privacy Matrix → Choose preset or customize",
                "tips": ["Public, Friends Only, or Private", "Control who sees content", "Manage comment permissions"]
            },
            {
                "step_number": 3,
                "title": "Security Settings",
                "description": "Settings → Security → Enable 2FA, manage sessions, add biometrics",
                "tips": ["Always enable 2FA", "Logout unused devices", "Add Face ID/Touch ID"]
            }
        ],
        "next_topic": None
    }
}


@router.post("/guide", response_model=OnboardingResponse)
async def get_onboarding_guide(request: OnboardingRequest):
    """
    Get step-by-step onboarding guide for a specific topic
    """
    try:
        logger.info(f"Onboarding request for topic: {request.topic} from user {request.user_id}")
        
        topic = request.topic.lower()
        
        # Get predefined guide if available
        if topic in ONBOARDING_GUIDES:
            guide = ONBOARDING_GUIDES[topic]
            
            # If user has specific question, enhance with AI response
            if request.question:
                # Get user context if permissions granted
                user_context = await permission_service.get_user_context(request.user_id)
                
                # Get relevant documentation if available
                doc_context = ""
                if rag_service.is_initialized:
                    doc_context = await rag_service.get_relevant_context_string(
                        f"{topic} {request.question}",
                        k=2
                    )
                
                # Build enhanced prompt
                context_str = ""
                if user_context:
                    if "kyc_status" in user_context:
                        context_str += f"\nUser's KYC status: {user_context['kyc_status']}"
                
                ai_prompt = f"""User is learning about: {topic}

Their question: {request.question}
{context_str}

{doc_context}

Provide a clear, helpful answer specific to their question. Keep it concise and actionable."""

                messages = [{"role": "user", "content": ai_prompt}]
                ai_answer = await groq_service.generate_response(messages, request.user_id)
                
                # Add AI answer to overview
                guide["overview"] = f"{guide['overview']}\n\nAnswer to your question: {ai_answer}"
            
            return OnboardingResponse(
                topic=topic,
                overview=guide["overview"],
                steps=[OnboardingStep(**step) for step in guide["steps"]],
                next_topic=guide.get("next_topic")
            )
        
        else:
            # Topic not found, use AI to generate guide
            raise HTTPException(
                status_code=404,
                detail=f"Topic '{topic}' not found. Available: kyc, wallet, marketplace, cap, streaming, profile"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting onboarding guide: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/help", response_model=QuickHelpResponse)
async def quick_help(request: QuickHelpRequest):
    """
    Get quick help for any question about the app
    """
    try:
        logger.info(f"Quick help request from user {request.user_id}: {request.query}")
        
        # Get user context
        user_context = await permission_service.get_user_context(request.user_id)
        
        # Get relevant docs
        doc_context = ""
        if rag_service.is_initialized:
            doc_context = await rag_service.get_relevant_context_string(
                request.query,
                k=3
            )
        
        # Build context string
        context_parts = []
        if user_context:
            if "kyc_status" in user_context:
                context_parts.append(f"User's KYC: {user_context['kyc_status']}")
            if "wallet_balance" in user_context:
                context_parts.append(f"Wallet balance: ${user_context['wallet_balance']}")
        
        context_str = "\n".join(context_parts) if context_parts else ""
        
        # Build help prompt
        help_prompt = f"""User question: {request.query}

{context_str}

{doc_context}

Provide a clear, helpful, step-by-step answer. Be specific and actionable. If the question is about user's specific data (KYC, wallet, etc.), reference their actual status."""

        messages = [{"role": "user", "content": help_prompt}]
        answer = await groq_service.generate_response(messages, request.user_id)
        
        # Identify related topics
        related = []
        query_lower = request.query.lower()
        if any(word in query_lower for word in ["kyc", "verify", "identity", "id"]):
            related.append("kyc")
        if any(word in query_lower for word in ["wallet", "money", "payment", "tip", "payout"]):
            related.append("wallet")
        if any(word in query_lower for word in ["marketplace", "buy", "sell", "escrow"]):
            related.append("marketplace")
        if any(word in query_lower for word in ["cap", "capture", "evidence", "camera", "photo"]):
            related.append("cap")
        if any(word in query_lower for word in ["stream", "live", "broadcast"]):
            related.append("streaming")
        if any(word in query_lower for word in ["profile", "settings", "privacy", "security"]):
            related.append("profile")
        
        return QuickHelpResponse(
            answer=answer,
            related_topics=list(set(related))[:3]  # Max 3 related topics
        )
        
    except Exception as e:
        logger.error(f"Error in quick help: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def get_available_topics():
    """Get list of available onboarding topics"""
    return {
        "topics": list(ONBOARDING_GUIDES.keys()),
        "descriptions": {
            topic: guide["title"] 
            for topic, guide in ONBOARDING_GUIDES.items()
        }
    }
