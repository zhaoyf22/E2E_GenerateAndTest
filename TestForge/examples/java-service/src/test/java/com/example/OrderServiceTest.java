package com.example;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class OrderServiceTest {

    private final OrderService service = new OrderService();

    @ParameterizedTest
    @CsvSource({"100,1,100", "100,3,300", "0,1,0"})
    void totalReturnsPriceTimesQuantity(int price, int quantity, int expected) {
        assertEquals(expected, service.total(price, quantity));
    }

    @ParameterizedTest
    @CsvSource({"-1,1", "100,0"})
    void totalRejectsInvalidInput(int price, int quantity) {
        assertThrows(IllegalArgumentException.class, () -> service.total(price, quantity));
    }
}
