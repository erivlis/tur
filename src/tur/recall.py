import json
import yaml
from pathlib import Path
import networkx as nx

def topological_recall(query: str, persona_dir: Path) -> str:
    """
    Upgraded recall logic under EP-0103.
    Searches the L2 knowledge graph, propagates spreading activation (2 hops),
    stages access metrics in a transient append-only log, and falls back to L1 if L2 is missing.
    """
    kg_path = persona_dir / 'knowledge_graph.yaml'
    if not kg_path.exists():
        # Frictionless Fallback: Basic L1 substring search
        from tur.memory import MemoryManager
        manager = MemoryManager(base_dir=persona_dir)
        mems = manager.load_all(include_archived=False)
        query_lower = query.lower()
        results = [m for m in mems if query_lower in m.content.lower() or any(query_lower in tag.lower() for tag in m.tags)]
        if not results:
            return f"No memories found matching query: '{query}'"
        mem_list = [{'id': str(m.id), 'type': m.type.value, 'content': m.content} for m in results]
        return json.dumps(mem_list, indent=2)

    try:
        with open(kg_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        graph = nx.node_link_graph(data)
    except Exception:
        # Fallback if graph is corrupted
        from tur.memory import MemoryManager
        manager = MemoryManager(base_dir=persona_dir)
        mems = manager.load_all(include_archived=False)
        query_lower = query.lower()
        results = [m for m in mems if query_lower in m.content.lower() or any(query_lower in tag.lower() for tag in m.tags)]
        if not results:
            return f"No memories found matching query: '{query}'"
        mem_list = [{'id': str(m.id), 'type': m.type.value, 'content': m.content} for m in results]
        return json.dumps(mem_list, indent=2)

    query_lower = query.lower()
    matched_nodes = []
    
    # 1. Retrieve relevant nodes via substring search
    for node, ndata in graph.nodes(data=True):
        if ndata.get("status") == "archived" or ndata.get("status") == "superseded":
            continue
        content = ndata.get("content", "").lower()
        if query_lower in node.lower() or query_lower in content:
            matched_nodes.append(node)

    if not matched_nodes:
        return f"No memories found matching query: '{query}'"

    # 2. Spreading Activation (2 hops)
    activated_nodes = set(matched_nodes)
    
    # Hop 1
    hop1 = set()
    for node in matched_nodes:
        neighbors = list(graph.successors(node)) + list(graph.predecessors(node))
        for n in neighbors:
            if graph.nodes[n].get("status") not in ["archived", "superseded"]:
                hop1.add(n)
    activated_nodes.update(hop1)
    
    # Hop 2
    hop2 = set()
    for node in hop1:
        neighbors = list(graph.successors(node)) + list(graph.predecessors(node))
        for n in neighbors:
            if graph.nodes[n].get("status") not in ["archived", "superseded"]:
                hop2.add(n)
    activated_nodes.update(hop2)

    # 3. Stage access metrics in a transient append-only log
    log_path = persona_dir / 'recall_access_log.txt'
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            for node in activated_nodes:
                f.write(f"{node}\n")
    except Exception:
        pass

    # Build results list
    results = []
    for node in activated_nodes:
        ndata = graph.nodes[node]
        results.append({
            'id': node,
            'type': ndata.get('type', 'Concept'),
            'content': ndata.get('content', '')
        })

    return json.dumps(results, indent=2)
