package ru.kubsu.main.exception;

import lombok.Getter;

@Getter
public class MinIOException extends RuntimeException {
    private final String field;

    public MinIOException(String message, Throwable cause) {
        super(message, cause);
        this.field ="minIOException";
    }

}
