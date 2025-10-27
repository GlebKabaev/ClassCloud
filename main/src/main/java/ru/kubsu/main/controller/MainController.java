package ru.kubsu.main.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import ru.kubsu.main.service.TraineeService;


@RestController
@RequiredArgsConstructor
@RequestMapping("/main")
public class MainController {
    private final TraineeService traineeService;

    @PostMapping("/trainee/{objectName}")
    public ResponseEntity<String> post(@PathVariable String objectName) {

        return ResponseEntity.ok(traineeService.executeTrainee(objectName));
    }

}
