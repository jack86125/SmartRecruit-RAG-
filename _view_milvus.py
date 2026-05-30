from pymilvus import MilvusClient

c = MilvusClient(uri="http://localhost:19530")
print("Milvus 集合:", c.list_collections())

res = c.query(
    "resume_embeddings",
    filter="id != ''",
    limit=5,
    output_fields=["id","doc_hash","text","work_experience","age","name","gender"]
)
print(f"返回行数: {len(res)}")
for i, r in enumerate(res):
    print(f"\n--- 记录 {i+1} ---")
    print(f"  ID: {r['id']}")
    print(f"  Hash: {r.get('doc_hash','N/A')[:30]}...")
    print(f"  姓名: {r.get('name','N/A')}")
    print(f"  性别: {r.get('gender','N/A')}")
    print(f"  年龄: {r.get('age','N/A')}")
    print(f"  工作经验: {r.get('work_experience','N/A')}年")
    print(f"  文本片段: {r.get('text','')[:120]}...")
