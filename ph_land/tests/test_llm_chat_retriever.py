import app.llm.core.llm_chat as llm_chat


def test_get_or_create_retriever_retries_after_transient_failure(monkeypatch):
    calls = {"count": 0}

    class DummyRetriever:
        def invoke(self, query):
            return ["doc-for-" + query]

    def fake_get_retriever(k=4):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary failure")
        return DummyRetriever()

    monkeypatch.setattr(llm_chat, "_retriever", None)
    monkeypatch.setattr(llm_chat, "get_retriever", fake_get_retriever)

    first = llm_chat._get_or_create_retriever()
    assert isinstance(first, llm_chat._SafeRetriever)

    second = llm_chat._get_or_create_retriever()
    assert calls["count"] == 2
    assert not isinstance(second, llm_chat._SafeRetriever)
    assert second.invoke("hello") == ["doc-for-hello"]


def test_retrieve_docs_supports_langchain_invoke_api():
    class DummyRetriever:
        def invoke(self, query):
            return ["doc-for-" + query]

    docs = llm_chat._retrieve_docs(DummyRetriever(), "hello")
    assert docs == ["doc-for-hello"]
