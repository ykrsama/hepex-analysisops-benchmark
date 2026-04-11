from engine.llm_judge import OpenAIJudge, get_judge


def test_get_judge_defaults_to_openai(monkeypatch):
    monkeypatch.delenv("HEPEX_JUDGE_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("HEPEX_OPENAI_MODEL", "gpt-5")

    judge = get_judge()

    assert isinstance(judge, OpenAIJudge)
    assert judge.model == "gpt-5"
