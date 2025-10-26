package ru.kubsu.main.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;

@RestController
@RequestMapping("/main")
public class MainController {

    @PostMapping("/trainee")
    public ResponseEntity<?> post(@RequestPart MultipartFile file) {

        return  ResponseEntity.ok().build();
    }

}
