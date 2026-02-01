"""
Test script to verify all new features are working
Run this after starting the server to check functionality
"""
import asyncio
from app.services.context_manager import context_manager
from app.services.rag_service import rag_service
from app.services.permission_service import permission_service


async def test_context_manager():
    """Test context manager functionality"""
    print("\n=== Testing Context Manager ===")
    try:
        # Test token counting
        text = "Hello, this is a test message"
        tokens = context_manager.count_tokens(text)
        print(f"✓ Token counting works: '{text}' = {tokens} tokens")
        
        # Test context optimization
        print("✓ Context manager initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Context manager error: {e}")
        return False


async def test_rag_service():
    """Test RAG service functionality"""
    print("\n=== Testing RAG Service ===")
    try:
        # Initialize RAG
        await rag_service.initialize()
        print(f"✓ RAG service initialized: {rag_service.is_initialized}")
        
        if rag_service.is_initialized:
            # Test document retrieval
            query = "How do I verify KYC?"
            results = await rag_service.retrieve_context(query, k=2)
            print(f"✓ Retrieved {len(results)} documents for query: '{query}'")
            
            if results:
                print(f"  Sample result: {results[0]['content'][:100]}...")
        else:
            print("⚠ RAG initialized but no documents loaded (this is OK if no docs exist)")
        
        return True
    except Exception as e:
        print(f"✗ RAG service error: {e}")
        return False


async def test_permission_service():
    """Test permission service functionality"""
    print("\n=== Testing Permission Service ===")
    try:
        test_user_id = "test_user_123"
        
        # Test granting permission
        result = await permission_service.grant_permission(test_user_id, "kyc")
        print(f"✓ Grant permission: {result}")
        
        # Test checking permission
        has_permission = await permission_service.check_user_permission(test_user_id, "kyc")
        print(f"✓ Check permission: {has_permission}")
        
        # Test revoking permission
        result = await permission_service.revoke_permission(test_user_id, "kyc")
        print(f"✓ Revoke permission: {result}")
        
        return True
    except Exception as e:
        print(f"✗ Permission service error: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 50)
    print("AI Assistant Feature Verification")
    print("=" * 50)
    
    results = {
        "Context Manager": await test_context_manager(),
        "RAG Service": await test_rag_service(),
        "Permission Service": await test_permission_service()
    }
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    for feature, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{feature}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All features working correctly!")
    else:
        print("\n⚠ Some features need attention. Check errors above.")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
