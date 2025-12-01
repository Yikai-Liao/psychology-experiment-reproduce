import unittest

import main


class MCPWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure previous tests cannot leak state.
        self.prompts_log: list[str] = []
        self._call_tool("init", main.init.fn)

    def _call_tool(self, label: str, tool_fn, *args):
        """Invoke an MCP tool function, log, and return its output."""
        result = tool_fn(*args)
        entry = f"{label}: {result}"
        print(entry)
        self.prompts_log.append(entry)
        return result

    def _advance_base_steps(self) -> None:
        """Advance through all base (non-experiment) prompts."""
        for idx, _ in enumerate(main.base_keys):
            self._call_tool(f"next_step base[{idx}]", main.next_step.fn)

    def test_base_prompts_follow_declared_order(self) -> None:
        outputs = [
            self._call_tool(f"next_step base[{idx}]", main.next_step.fn)
            for idx, _ in enumerate(main.base_keys)
        ]
        expected = [main.prompts[key].strip() for key in main.base_keys]
        self.assertEqual(outputs, expected)

        # After finishing base prompts, next_step should request experiments.
        message = self._call_tool("next_step post-base", main.next_step.fn)
        self.assertIn("Set experiments first", message)

    def test_experiment_prompts_enforce_declared_sequence(self) -> None:
        self._advance_base_steps()
        self._call_tool("set_experiments", main.set_experiments.fn, ["exp1", "exp2"])

        # Cannot jump ahead to exp2 before exp1 is finished.
        blocked = self._call_tool("experiment_step exp2 blocked", main.experiment_step.fn, "exp2")
        self.assertIn("Next experiment in sequence is 'exp1'", blocked)

        impl_1 = self._call_tool("experiment_step exp1 impl", main.experiment_step.fn, "exp1")
        self.assertIn("Implementation", impl_1)

        exec_1 = self._call_tool("experiment_step exp1 exec", main.experiment_step.fn, "exp1")
        self.assertIn("Code Execution", exec_1)

        impl_2 = self._call_tool("experiment_step exp2 impl", main.experiment_step.fn, "exp2")
        self.assertIn("Implementation", impl_2)

        exec_2 = self._call_tool("experiment_step exp2 exec", main.experiment_step.fn, "exp2")
        self.assertIn("Code Execution", exec_2)

        report_prompt = self._call_tool("next_step report", main.next_step.fn)
        self.assertIn("Step 4: Report", report_prompt)
        final_msg = self._call_tool("next_step final", main.next_step.fn)
        self.assertEqual("All prompts have been delivered.", final_msg)


if __name__ == "__main__":
    unittest.main()
