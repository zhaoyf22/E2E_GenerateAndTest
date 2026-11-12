package com.example;

public class OrderService {

    public int total(int price, int quantity) {
        if (price < 0 || quantity < 1) {
            throw new IllegalArgumentException("price must be >= 0 and quantity >= 1");
        }
        return price * quantity;
    }
}
