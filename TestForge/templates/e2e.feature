# language: zh-CN
@e2e @order
Feature: 下单与支付

  Background:
    Given 已存在用户 "buyer+001@example.com" 且邮箱已验证
    And 商品 "SKU-001" 库存为 10，单价 99.00

  @priority:P0 @technique:scenario
  Scenario: 已登录用户购买单件商品并支付成功
    Given 用户 "buyer+001@example.com" 已登录
    And 购物车中 "SKU-001" 数量为 1
    When 用户进入结算页并选择"在线支付"
    And 用户提交订单
    Then 页面跳转到 "/orders/{orderId}"
    And 订单状态显示"待支付"
    When 用户完成支付
    Then 订单状态显示"已支付"
    And 商品 "SKU-001" 库存变为 9

  @priority:P0 @technique:EP
  Scenario: 库存不足时提交订单被拒绝
    Given 用户 "buyer+001@example.com" 已登录
    And 商品 "SKU-001" 库存为 1
    And 购物车中 "SKU-001" 数量为 2
    When 用户提交订单
    Then 页面提示"库存不足"
    And 商品 "SKU-001" 库存仍为 1
    And 用户没有新订单

  @priority:P1 @technique:permission
  Scenario: 未登录用户提交订单被重定向到登录页
    Given 用户未登录
    And 购物车中 "SKU-001" 数量为 1
    When 用户提交订单
    Then 页面跳转到 "/login?redirect=/checkout"
    And 没有创建订单
