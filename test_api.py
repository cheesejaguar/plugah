#!/usr/bin/env python3
"""
Test script to validate the stable API surface for Seren integration
"""

import asyncio
import os
import sys
from pathlib import Path


async def test_api():
    """Test the complete API surface"""
    
    # Set mock mode for testing
    os.environ["PLUGAH_MODE"] = "mock"
    
    print("Testing Plugah API surface...")
    print("-" * 50)
    
    # Test 1: Basic imports
    print("1. Testing imports...")
    try:
        from plugah import BoardRoom, BudgetPolicy
        print("   ✓ BoardRoom imported")
        print("   ✓ BudgetPolicy imported")
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Test 2: Additional imports
    print("\n2. Testing additional imports...")
    try:
        from plugah import (
            ExecutionResult,
            PRD,
            OAG,
            PlugahError,
            InvalidInput,
            BudgetExceeded,
            ProviderError,
            Event,
        )
        print("   ✓ All types imported successfully")
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Test 3: BoardRoom initialization
    print("\n3. Testing BoardRoom initialization...")
    try:
        br = BoardRoom()
        print(f"   ✓ BoardRoom created with project_id: {br.project_id}")
    except Exception as e:
        print(f"   ✗ BoardRoom creation failed: {e}")
        return False
    
    # Test 4: startup_phase
    print("\n4. Testing startup_phase...")
    try:
        questions = await br.startup_phase(
            problem="Build a test application",
            budget_usd=100.0,
            model_hint="gpt-6-luna",
            policy=BudgetPolicy.BALANCED,
        )
        print(f"   ✓ Generated {len(questions)} questions")
        assert isinstance(questions, list), "Questions should be a list"
        assert all(isinstance(q, str) for q in questions), "All questions should be strings"
    except Exception as e:
        print(f"   ✗ startup_phase failed: {e}")
        return False
    
    # Test 5: process_discovery
    print("\n5. Testing process_discovery...")
    try:
        answers = ["Test users", "Test criteria", "Test constraints", "ASAP", "None"]
        prd = await br.process_discovery(
            answers=answers,
            problem="Build a test application",
            budget_usd=100.0,
            model_hint="gpt-6-luna",
            policy="balanced",  # Test string policy
        )
        print(f"   ✓ PRD created with {len(prd.objectives)} objectives")
        assert isinstance(prd, PRD), "Should return PRD object"
        assert prd.to_dict() is not None, "PRD should have to_dict method"
    except Exception as e:
        print(f"   ✗ process_discovery failed: {e}")
        return False
    
    # Test 6: plan_organization
    print("\n6. Testing plan_organization...")
    try:
        oag = await br.plan_organization(
            prd=prd,
            budget_usd=100.0,
            model_hint="gpt-6-luna",
            policy=BudgetPolicy.CONSERVATIVE,
        )
        print(f"   ✓ OAG created with {len(oag.get_agents())} agents and {len(oag.get_tasks())} tasks")
        assert isinstance(oag, OAG), "Should return OAG object"
    except Exception as e:
        print(f"   ✗ plan_organization failed: {e}")
        return False
    
    # Test 7: execute
    print("\n7. Testing execute...")
    try:
        result = await br.execute()
        print(f"   ✓ Execution complete with total cost: ${result.total_cost}")
        assert isinstance(result, ExecutionResult), "Should return ExecutionResult"
        assert hasattr(result, "total_cost"), "Result should have total_cost"
        assert hasattr(result, "artifacts"), "Result should have artifacts"
        assert hasattr(result, "metrics"), "Result should have metrics"
        assert hasattr(result, "details"), "Result should have details"
    except Exception as e:
        print(f"   ✗ execute failed: {e}")
        return False
    
    # Test 8: State persistence
    print("\n8. Testing state persistence...")
    try:
        # Save state
        state_file = Path("test_state.json")
        br.save_state(state_file)
        print(f"   ✓ State saved to {state_file}")
        
        # Load state
        br2 = BoardRoom()
        br2.load_state(state_file)
        print(f"   ✓ State loaded from {state_file}")
        
        # Clean up
        state_file.unlink()
        
        # Test to_dict/from_dict
        state_dict = br.to_dict()
        br3 = BoardRoom.from_dict(state_dict)
        print("   ✓ to_dict/from_dict working")
    except Exception as e:
        print(f"   ✗ State persistence failed: {e}")
        return False
    
    # Test 9: Exception handling
    print("\n9. Testing exception handling...")
    try:
        br4 = BoardRoom()
        try:
            await br4.startup_phase("", 100.0)  # Empty problem
        except InvalidInput as e:
            print("   ✓ InvalidInput raised for empty problem")
        
        try:
            await br4.startup_phase("Test", -100.0)  # Negative budget
        except InvalidInput as e:
            print("   ✓ InvalidInput raised for negative budget")
        
        try:
            await br4.startup_phase("Test", 100.0, policy="invalid")  # Invalid policy
        except InvalidInput as e:
            print("   ✓ InvalidInput raised for invalid policy")
    except Exception as e:
        print(f"   ✗ Exception handling failed: {e}")
        return False
    
    # Test 10: Event streaming
    print("\n10. Testing event streaming...")
    try:
        events = []
        async for event in br.events_stream():
            events.append(event)
        print(f"   ✓ Streamed {len(events)} events")
        if events:
            assert all(isinstance(e, Event) for e in events), "All should be Event objects"
    except Exception as e:
        print(f"   ✗ Event streaming failed: {e}")
        return False
    
    # Test 11: Execute with explicit OAG
    print("\n11. Testing execute with explicit OAG...")
    try:
        br5 = BoardRoom()
        result2 = await br5.execute(oag=oag)
        print(f"   ✓ Execution with explicit OAG complete: ${result2.total_cost}")
    except Exception as e:
        print(f"   ✗ Execute with OAG failed: {e}")
        return False
    
    # Test 12: JSON Schema access
    print("\n12. Testing JSON Schema access...")
    try:
        prd_schema = prd.get_json_schema()
        print(f"   ✓ PRD JSON Schema available with {len(prd_schema['properties'])} properties")
        
        oag_schema = oag.model_json_schema()
        print(f"   ✓ OAG JSON Schema available")
    except Exception as e:
        print(f"   ✗ JSON Schema access failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All API tests passed!")
    return True


async def test_compatibility_snippet():
    """Test the exact compatibility snippet from the request"""
    
    print("\n" + "=" * 50)
    print("Testing Seren compatibility snippet...")
    print("-" * 50)
    
    os.environ["PLUGAH_MODE"] = "mock"
    
    try:
        from plugah import BoardRoom, BudgetPolicy
        
        problem = "Build a test application"
        budget_usd = 100.0
        
        # Test the exact integration surface
        br = BoardRoom()
        
        # Phase 1
        questions = await br.startup_phase(problem, budget_usd)
        print(f"✓ startup_phase returned {len(questions)} questions")
        
        # Phase 2
        answers = ["Test answer"] * len(questions)
        prd = await br.process_discovery(answers, problem, budget_usd)
        print(f"✓ process_discovery returned PRD")
        
        # Phase 3
        oag = await br.plan_organization(prd, budget_usd)
        print(f"✓ plan_organization returned OAG")
        
        # Phase 4
        result = await br.execute()
        print(f"✓ execute returned result with total_cost: ${result.total_cost}")
        
        print("\n✅ Seren compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Seren compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner"""
    
    print("Plugah API Surface Test Suite")
    print("=" * 50)
    
    # Run main API tests
    api_success = await test_api()
    
    # Run compatibility test
    compat_success = await test_compatibility_snippet()
    
    # Final result
    print("\n" + "=" * 50)
    if api_success and compat_success:
        print("🎉 All tests passed! API is ready for Seren integration.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())