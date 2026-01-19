---
title: Test
date: 2026-01-19 19:49:20 +0800
categories: ['LLM', 'Courses', '李宏毅']
tags: ['LLM', 'Reasoning Model', '李宏毅']
---

# Reasoning Models

# Introduction

## What are Reasoning Models?

- 有一系列的模型會有特定的”深度思考行為” → 這類模型稱為”Reasoning Model”
    - (ex) GPT o-series (o1, o1-mini, o3-mini) / DeepSeek r-series / Gemini 2.5 / Claude 3.7 Sonnet
- (ex) 1+1?

![Screenshot 2026-01-13 at 10.18.57 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_10.18.57_AM.png)

![Reasoning Model的”深度思考內容” — 可能包含反覆驗證/探索不同方法/planning](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_10.19.10_AM.png)

Reasoning Model的”深度思考內容” — 可能包含反覆驗證/探索不同方法/planning

- Reasoning Model的”深度思考內容 (i.e 推理)”, 可能會包含反覆檢視自己的答案 (Verification), 探索不同方法 (Explore), 對複雜問題先做規劃 (Planning)
    - 通常用`<think>`delimiter去區隔reasoning traces與output
    
    ![Screenshot 2026-01-13 at 12.35.34 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_12.35.34_PM.png)
    

---

## Test-Time Compute & Test-Time Scaling

- Reasoning Model背後的概念: Test-Time Compute — 在inference階段, 投入額外算力

![image.png](/assets/2026-01-19-reasoning-model/image.png)

- (ex) 在正式回答前, 使用額外的token先做Chain-of-Thought
- (ex) 嘗試多種解題的方式, 再選擇最好的解法

![image.png](/assets/2026-01-19-reasoning-model/image 1.png)

- Test-Time Compute可能造成”Test-Time Scaling” — Inference投注的額外計算資源越多, 結果越好

![[https://arxiv.org/pdf/2501.19393](https://arxiv.org/pdf/2501.19393)](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-18_at_12.23.47_PM.png)

[https://arxiv.org/pdf/2501.19393](https://arxiv.org/pdf/2501.19393)

- 有趣的觀察: 在相同模型表現下, 可以依靠將算力投注在Train-Time或Test-Time達成
    - 而且, 投注在Test-Time的算力往往比投注在Train-Time少很多, 是一個潛在的研究方向！

![虛線表示固定的表現: 在相同的表現下,  可以透過在train-time投注大量資源, 或選擇test-time投注大量資源](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_5.24.57_PM.png)

虛線表示固定的表現: 在相同的表現下,  可以透過在train-time投注大量資源, 或選擇test-time投注大量資源

---

# 打造Reasoning Model的方法

![Screenshot 2026-01-13 at 5.31.31 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_5.31.31_PM.png)

## Chain-of-Thought (CoT) → 適用於比較強的模型

- 可以透過Chain-of-Thought (CoT) 使模型先進行思考, 再開始回答
    - 請模型將reasoning放在<think> delimiter裡, 方便介面顯示
- 以CoT的方式產生reasoning, 背後並非在模型本質上有所改變 (ex: 訓練時鼓勵某些思考行為/好的思考過程), 而是採用prompting stragety去逼出模型接龍出思考流程
- 然而, 只有比較強的模型能使用CoT的方式產生合理的reasoning
    - 弱模型(ex: Llama 3)本身能力就不足, 無法採用該方式逼出更多的思考流程, 需要由強模型去教

---

- 透過CoT請模型做reasoning的方式, 一開始是在prompt裡給幾個reasoning的範例 → Few-Shot CoT
- 後來, 研究發現直接請模型”think step by step”就可以做到不錯的reasoning → Zero-Shot CoT
- 通常Few-Shot CoT或Zero-Shot CoT產生的推理過程都比較簡短, 被稱為”Short CoT”。而reasoning model的推理過程叫”Long CoT”
    - 然而, 多長的推理才稱為Long, 並沒有共識

![Screenshot 2026-01-13 at 11.54.26 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_11.54.26_PM.png)

---

- 使CoT的推理過程變長的解決方式:
    - 研究發現: 將思考方式/流程在prompt裡定義的更仔細, 模型的推理就會跟著變長! → Supervised CoT

![Screenshot 2026-01-13 at 11.56.37 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_11.56.37_PM.png)

- 然而, 只要將思考方式/流程訂的更仔細, 寫在prompt裡, 模型的reasoning trace也會跟著變長! → Supervised CoT
    - 另外, 請模型將思考過程放在<think>裡, 方便介面顯示

![Screenshot 2026-01-13 at 11.56.37 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_11.56.37_PM.png)

![Screenshot 2026-01-13 at 11.58.22 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-13_at_11.58.22_PM.png)

![Screenshot 2026-01-14 at 12.00.40 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_12.00.40_AM.png)

---

## 採用多次不同的推理路徑 → 弱模型也可以適用

- 請模型對同個問題生成N次 (reasoning/output) → 達到”Explore”的效果

![Screenshot 2026-01-14 at 8.13.05 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_8.13.05_AM.png)

- 研究顯示: 只要模型嘗試夠多次, 總有機會解到對的答案

![X軸: 嘗試解題的次數
Y軸: 各種嘗試中, 已經cover了多少正確答案過
可以看到, 比較沒那麼弱的模型, 在嘗試夠多次後, 總會有機會”賽到”正確的答案
而明顯非常弱的模型, 在多次嘗試後, 可能還是沒辦法](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_8.58.04_AM.png)

X軸: 嘗試解題的次數
Y軸: 各種嘗試中, 已經cover了多少正確答案過
可以看到, 比較沒那麼弱的模型, 在嘗試夠多次後, 總會有機會”賽到”正確的答案
而明顯非常弱的模型, 在多次嘗試後, 可能還是沒辦法

---

- Q: 那要怎麼決定, 多次生成後, 最終要output哪個答案？
- 最直覺的是採用Majority Vote (Self-Consistency)

![Screenshot 2026-01-14 at 9.04.24 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_9.04.24_AM.png)

- Majority vote的概念雖然很簡單, 但表現意外的強大 → 比較test-time compute的方法時, Baseline可以採用majority vote (不容易打敗)
    
    ![1B的模型在做majority vote後, 表現比起0-shot CoT (think step by step)好很多, 且與8B 0-shot的距離接近了](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_9.54.32_AM.png)
    
    1B的模型在做majority vote後, 表現比起0-shot CoT (think step by step)好很多, 且與8B 0-shot的距離接近了
    

---

- 除了以majority vote的方式決定最終結果外, 另個方法是使用verifier去判斷答案是否正確
    - Model Output → Verifier → Score
    - Verifier也是個LLM
    
    ![Screenshot 2026-01-19 at 9.21.31 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-19_at_9.21.31_AM.png)
    
- 有了verifier後, 再選擇verifier分數最高的答案 → Best-of-N strategy

![Screenshot 2026-01-14 at 12.21.22 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_12.21.22_PM.png)

---

- Q: 如何得到verifier LLM?
    - Option 1: 直接使用比較強的LLM → 現在語言模型大多具有”反思”的能力
    - Option 2: 訓練一個verifier LLM
        - 建立 (input, ground truth) dataset

![Screenshot 2026-01-14 at 12.23.50 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_12.23.50_PM.png)

---

- 讓模型多次生成 → 決定最終output的方法, 有兩種架構:
    - Parallel vs Sequential
    
    ![Screenshot 2026-01-14 at 1.17.36 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_1.17.36_PM.png)
    
    - 也可以將parallel和sequential結合起來
    
    ![Screenshot 2026-01-14 at 1.19.01 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_1.19.01_PM.png)
    

---

- 剛剛的方法們, 都是採用 — 模型先得到答案, 再丟到verifier進行驗證
- 但現在的reasoning model都是邊進行reason, 邊對中間的步驟進行驗證 → 避免時間浪費在錯誤的方法上

![Screenshot 2026-01-14 at 1.22.41 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_1.22.41_PM.png)

---

- 目前reasoning model並不是採用這種”做多次生成再產output”的方式 → 但以現在這方式, 如何變成對中間步驟直接做驗證?
- 其中一種方式:
    - 在每次生成時, 都先做一個step, 並在step結束後, 進行verifier (驗證該step是否合理)
    - 只有在step合理下, 才繼續往下做

![Screenshot 2026-01-14 at 2.44.16 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_2.44.16_PM.png)

![Screenshot 2026-01-14 at 2.43.27 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-14_at_2.43.27_PM.png)

- 如何得到Process Verifier?
    - 33:04

---

- 以下兩種方法 (Imitation Learning / RL) 可以視為後訓練 (post-training)的特例方法
- 
- 
- 以下兩個方式, 可以視為後訓練(post-training)的特例 → Foundation Model還沒有思考能力, 透過後訓練, 教它如何做reasoning
- [https://pytorch.org/blog/a-primer-on-llm-post-training/](https://pytorch.org/blog/a-primer-on-llm-post-training/)

## Imitation Learning (教模型 推理的過程 — 需要微調)

- 直接教模型怎麼做推理
    - Training data給（Input, Reasoning Process, Ground Truth）
    - 模型的任務是要output出reasoning + ground truth
- 然而, 最困難的是, reasoning process要怎麼得到? (通常, 有ground truth是簡單的, 但reasoning過程不容易取得)

![Screenshot 2026-01-16 at 2.53.28 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_2.53.28_PM.png)

- 通常, 可以請人標註 reasoning, 但很labor intensive
- 如果沒有, 怎麼做呢？

---

- 想辦法生成reasoning的訓練資料:
    - 我們有 (input, ans), 想要reasoning
    - 假設ans是對的, reasoning就是對的
    - 取出ans是對的的reasoning process, 合成 (input, reasoning, ans)作為training data
    - Verifier做的事:
        - 驗證答案是不是對的 (如果沒有標準答案)
        - 可以使用現成的LLM
    
    ![Screenshot 2026-01-16 at 5.02.08 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_5.02.08_PM.png)
    

- 有可能: 推論是錯的, 但結果是對的
- 因此, 就有人提出跟前一section介紹的”樹狀搜尋”的方式 — 雷同的方法去進行reasoning的驗證
    - 每一個step都有一個process verifier進行驗證, 是否是好的步驟
    
    ![Screenshot 2026-01-16 at 5.05.51 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_5.05.51_PM.png)
    

---

- 這類的方法, 看起來其實就是supervised finetuning (給定input/output, 去fintune), 為什麼特別叫做imitation learning呢
- 其實, initiation learning也可以做成reinforcement learning

![使用RL的話, 可能是: 
- 提高綠色step 1機率, 降低藍色step 1機率
- 提高綠色step chain機率, 降低其他chain機率](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_5.10.47_PM.png)

使用RL的話, 可能是: 
- 提高綠色step 1機率, 降低藍色step 1機率
- 提高綠色step chain機率, 降低其他chain機率

---

- 然而, 好的reasoning model, 推理過程每一步都要是對的嗎？
    - 過程有可能有幾步是錯的 → 發現問題/修改 → 正確答案

![Screenshot 2026-01-16 at 5.25.31 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_5.25.31_PM.png)

- 因此, 如果給模型訓練的reasoning過程全都是對的, 反而會阻礙模型自我校正的能力！

![Screenshot 2026-01-16 at 5.31.42 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_5.31.42_PM.png)

- 因此, 可以刻意製造一些錯誤過程
    - 在reasoning tree中, 做深度優先的搜尋, 把錯誤的過程也包含在訓練資料裡
    - 錯誤的step之後, 可以插入verifier的feedback, 讓整個reasoning trace顯得順暢

![Screenshot 2026-01-16 at 11.10.45 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_11.10.45_PM.png)

- 另一篇paper也佐證:
    - Shortcut Learning: （直接選擇一路上都是正確的推理路徑 → 模型學回順風局的回答）
    - Journey Learning: (有錯誤→正確的繞路 → 模型學會逆轉勝)
    - Journey Learning表現的比Shortcut Learning好
    
    ![Screenshot 2026-01-16 at 11.21.02 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_11.21.02_PM.png)
    

---

- 不過現在, 想自己打造reasoning model或許已經不用那麼麻煩, 因為已經存在不少有能力做reasoning的模型
- Knowledge Distillation
    
    ![Screenshot 2026-01-16 at 11.39.17 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_11.39.17_PM.png)
    

![利用DeepSeek-R1作為reasoning model的老師, 去distill 較弱的模型, 大幅提升這些模型的表現](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-16_at_11.45.10_PM.png)

利用DeepSeek-R1作為reasoning model的老師, 去distill 較弱的模型, 大幅提升這些模型的表現

---

## Reinforcement Learning (以結果為導向的去學習推理 — 需要微調)

- 以結果為導向 → DeepSeek R1系列的做法
- 有(input, ground truth)
- 模型的reasoning process如果最後得到的答案是對的 → positive feedback
- 反之, 如果得到的答案是錯的 → negative feedback
- 因此, 在RL以結果為導向的方法中, 推論過程不重要, 答案是對的就好
- 與Imitation Learning不同的是, imitation learning著重在過程是否也正確, 但在RL以結果為導向的方法中, 答案對就好

![Screenshot 2026-01-17 at 9.01.30 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_9.01.30_AM.png)

- DeepSeek-R1-Zero: 並非我們平常用到的DeepSeek  — 這是個純粹用RL學出來的模型
- 以DeepSeek-v3-base作為Foundation Model, 並以accuracy和format(要產生<think> token)作為reward

![Screenshot 2026-01-17 at 9.05.35 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_9.05.35_AM.png)

---

- 這種方式的結果好不好呢?
- 可以看到: 今天介紹的幾種方法是沒有衝突的, 可以合起來使用 (ex) Foundation Model → Post Training (RL → Majority Vote)

![以R1-zero來說, 藍色的線表示只做一次reasoning+inference, 在RL訓練step逐漸增加時, 會逼近o1 
而如果允許R1-zero做多次reasoning+inference, 並使用majority vote, 其結果可以甚至超越o1做majority vote ](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_9.14.37_AM.png)

以R1-zero來說, 藍色的線表示只做一次reasoning+inference, 在RL訓練step逐漸增加時, 會逼近o1 
而如果允許R1-zero做多次reasoning+inference, 並使用majority vote, 其結果可以甚至超越o1做majority vote 

![模型在reasoning時, 依靠RL(而沒有人為介入), 得到了aha moment ](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_9.22.46_AM.png)

模型在reasoning時, 依靠RL(而沒有人為介入), 得到了aha moment 

---

- 為什麼R1-Zero沒有放在平台上讓大家使用呢?
- 因為reasoning過程的readability太差
    - 在訓練時, 只看結果, 而不重視reasoning process, 導致雖然做的好, 但reasoning process的可讀性並沒有被加強!

![Screenshot 2026-01-17 at 11.03.52 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.03.52_AM.png)

---

![首先, 從已經有(reasoning可讀性很差的)DeepSeek-R1-zero, 可以得到(Input, Reasoning Process, Ground Truth)
再透過大量的人力, 將reasoning process做human annotation, 改成可讀性較佳的版本
接著, 使用改寫後的(Input, Reasoning Process, Ground Truth)去做Imitation Learning 

除了Human Annotation外, 也採用supervised CoT的方式, few-shot prompting及direct prompting for reflection/verification去產生reasoning過程 (幾千筆資料就好)

透過這些調整, 從DeepSeek-v3-base產生Model A ](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.12.01_AM.png)

首先, 從已經有(reasoning可讀性很差的)DeepSeek-R1-zero, 可以得到(Input, Reasoning Process, Ground Truth)
再透過大量的人力, 將reasoning process做human annotation, 改成可讀性較佳的版本
接著, 使用改寫後的(Input, Reasoning Process, Ground Truth)去做Imitation Learning 

除了Human Annotation外, 也採用supervised CoT的方式, few-shot prompting及direct prompting for reflection/verification去產生reasoning過程 (幾千筆資料就好)

透過這些調整, 從DeepSeek-v3-base產生Model A 

![接著, 在從Model A出發, 以Accuracy及語言的coherence (reasoning需要為同個語言)為reward, 使用RL去訓練出Model B](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.22.33_AM.png)

接著, 在從Model A出發, 以Accuracy及語言的coherence (reasoning需要為同個語言)為reward, 使用RL去訓練出Model B

![現在, Model B已經具有一定的reasoning能力了 → 但目前訓練的task主要集中在程式及數學等有標準答案的task上
下一步: 拓展到沒有標準答案的task上, 用Model B產生reasoning process, 並採用DeepSeek-v3作為verifier
再用一些heuristic去掉一些不想要的reasoning process (ex: 混合語言/太長/有code block …)
最後, 得到新的training data: (input, reasoning process, ans), 去做imitation learning, 將deepseek-v3-base訓練成Model C

最後, 再以safety/helpfulness作為reward, 透過RL將Model C轉成DeepSeek-R1 ](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.29.00_AM.png)

現在, Model B已經具有一定的reasoning能力了 → 但目前訓練的task主要集中在程式及數學等有標準答案的task上
下一步: 拓展到沒有標準答案的task上, 用Model B產生reasoning process, 並採用DeepSeek-v3作為verifier
再用一些heuristic去掉一些不想要的reasoning process (ex: 混合語言/太長/有code block …)
最後, 得到新的training data: (input, reasoning process, ans), 去做imitation learning, 將deepseek-v3-base訓練成Model C

最後, 再以safety/helpfulness作為reward, 透過RL將Model C轉成DeepSeek-R1 

- 由於DeepSeek訓練過程, 人工介入的部分並不算多, reasoning過程還是常常不太符合人類理解範圍

![Screenshot 2026-01-17 at 11.38.40 AM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.38.40_AM.png)

---

- 然而, 從研究結果也顯示, 以RL去訓練reasoning model, 很吃原先foundation model的能力

![如果以Qwen-32B-Base作為foundation model, 就無法靠RL強化base model的能力
反而以Imitation Learning (distillation)的方式, 對這種弱一點的模型強化會比較有效](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.49.21_AM.png)

如果以Qwen-32B-Base作為foundation model, 就無法靠RL強化base model的能力
反而以Imitation Learning (distillation)的方式, 對這種弱一點的模型強化會比較有效

- RL只是強化模型原有的能力 → 模型產生正確答案時, 增加正確答案的機率 (因此, 前提是原先就能夠產生正確答案！)

![研究顯示, 這些靠RL就可以表現更好的模型, 原本就有產生aha moment及反思的可能性, RL只是強化了這樣的機率](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_11.54.03_AM.png)

研究顯示, 這些靠RL就可以表現更好的模型, 原本就有產生aha moment及反思的可能性, RL只是強化了這樣的機率

---

- Reasoning Model的挑戰:
    - Reasoning是非常耗算力的
    - 是否能變成該reason時才reason?

![Screenshot 2026-01-17 at 4.52.25 PM.png](/assets/2026-01-19-reasoning-model/Screenshot_2026-01-17_at_4.52.25_PM.png)