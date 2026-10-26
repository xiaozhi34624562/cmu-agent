from __future__ import annotations

import math
import torch


def group_advantages(
    rewards: torch.Tensor,
    eps: float = 1e-8,
) -> torch.Tensor:
    """每行代表同一题的一组奖励；使用总体标准差，返回停止梯度的优势。"""
    if rewards.ndim != 2 or rewards.shape[0] == 0 or rewards.shape[1] < 2:
        raise ValueError("rewards 必须为非空 [num_prompts, group_size]，且组大小 >= 2")
    if not math.isfinite(eps) or eps <= 0:
        raise ValueError("eps 必须是有限正数")
    r = rewards.detach().to(dtype=torch.float32)
    if not torch.isfinite(r).all().item():
        raise ValueError("奖励包含 NaN 或无穷值；评分故障应先单独处理")
    mean = r.mean(dim=-1, keepdim=True)
    std = r.std(dim=-1, keepdim=True, unbiased=False)
    return (r - mean) / (std + eps)


def policy_loss(
    new_logp: torch.Tensor,
    behavior_logp: torch.Tensor,
    advantage: torch.Tensor,
    response_mask: torch.Tensor,
    mode: str = "ppo",
    lower: float = 0.8,
    upper: float = 1.2,
) -> torch.Tensor:
    """教学用 token 平均损失。所有张量形状必须为 [batch, time]。"""
    shape = new_logp.shape
    inputs = (behavior_logp, advantage, response_mask)
    if new_logp.ndim != 2 or any(x.shape != shape for x in inputs):
        raise ValueError("输入必须具有相同的二维 [batch, time] 形状")
    if any(x.device != new_logp.device for x in inputs):
        raise ValueError("所有输入必须位于同一设备")
    if response_mask.dtype != torch.bool:
        raise TypeError("response_mask 必须是布尔张量")
    if not all(x.is_floating_point() for x in
               (new_logp, behavior_logp, advantage)):
        raise TypeError("log-prob 和 advantage 必须是浮点张量")
    if (not math.isfinite(lower) or not math.isfinite(upper)
            or not (0 <= lower < 1 < upper)):
        raise ValueError("裁剪边界必须满足 0 <= lower < 1 < upper")
    if mode not in ("ppo", "cispo"):
        raise ValueError("mode 必须为 'ppo' 或 'cispo'")
    if not response_mask.any().item():
        raise ValueError("本批没有有效的策略生成 token")

    # 先选择有效 token，避免 padding 上的 NaN、-inf 参与后续运算。
    lp = new_logp[response_mask].float()
    old_lp = behavior_logp.detach()[response_mask].float()
    adv = advantage.detach()[response_mask].float()
    if not all(torch.isfinite(x).all().item() for x in (lp, old_lp, adv)):
        raise ValueError("有效 token 中存在非有限数值")
    if (lp > 1e-6).any().item() or (old_lp > 1e-6).any().item():
        raise ValueError("输入应是规范化分布的 log-prob，而非原始 logits")

    ratio = torch.exp(lp - old_lp)
    if not torch.isfinite(ratio).all().item():
        raise FloatingPointError("重要性比率溢出，请检查概率定义或策略差异")
    clipped = ratio.clamp(min=lower, max=upper)

    if mode == "ppo":
        objective = torch.minimum(ratio * adv, clipped * adv)
    else:
        # CISPO 的关键：权重固定，梯度只通过当前动作的 log-prob。
        objective = clipped.detach() * adv * lp

    return -objective.mean()


def scalar_gradient(mode: str, old_p: float, new_p: float, adv: float) -> float:
    new_lp = torch.tensor([[math.log(new_p)]], requires_grad=True)
    old_lp = torch.tensor([[math.log(old_p)]], requires_grad=True)
    advantage = torch.tensor([[adv]], requires_grad=True)
    mask = torch.ones((1, 1), dtype=torch.bool)
    loss = policy_loss(new_lp, old_lp, advantage, mask, mode=mode)
    loss.backward()
    assert old_lp.grad is None, "行为概率不应收到梯度"
    assert advantage.grad is None, "优势不应收到策略损失梯度"
    return float(new_lp.grad.item())


def main() -> None:
    # 奖励 [1, 0, 0, 0] 的总体标准差归一化结果。
    a = group_advantages(torch.tensor([[1., 0., 0., 0.], [1., 1., 1., 1.]]))
    expected = torch.tensor([math.sqrt(3), *([-1 / math.sqrt(3)] * 3)])
    assert torch.allclose(a[0], expected, atol=1e-6)
    assert torch.equal(a[1], torch.zeros(4))

    # 正优势、超过上界：PPO 饱和，CISPO 保留梯度。
    assert math.isclose(scalar_gradient("ppo", 0.4, 0.7, 1.), 0., abs_tol=1e-6)
    assert math.isclose(scalar_gradient("cispo", 0.4, 0.7, 1.), -1.2, abs_tol=1e-6)

    # 负优势、低于下界：PPO 饱和；CISPO 仍按裁剪权重抑制动作。
    assert math.isclose(scalar_gradient("ppo", 0.4, 0.2, -1.), 0., abs_tol=1e-6)
    assert math.isclose(scalar_gradient("cispo", 0.4, 0.2, -1.), 0.8, abs_tol=1e-6)

    # 坏动作概率增长到 1.5 倍，PPO 仍然施加惩罚。
    assert math.isclose(scalar_gradient("ppo", 0.4, 0.6, -1.), 1.5, abs_tol=1e-6)

    # 未被选择的 padding 不得污染 loss，也不能获得梯度。
    new_lp = torch.tensor([[math.log(0.4), float("nan")]], requires_grad=True)
    old_lp = torch.tensor([[math.log(0.4), float("nan")]])
    adv = torch.tensor([[1., float("nan")]])
    mask = torch.tensor([[True, False]])
    loss = policy_loss(new_lp, old_lp, adv, mask)
    assert torch.isfinite(loss).item()
    loss.backward()
    assert torch.allclose(new_lp.grad, torch.tensor([[-1., 0.]]), atol=1e-6)

    print("PPO/CISPO、组优势、停止梯度与 padding 掩码测试通过。")


if __name__ == "__main__":
    main()
