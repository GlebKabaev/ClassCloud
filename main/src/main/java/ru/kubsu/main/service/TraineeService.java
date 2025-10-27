package ru.kubsu.main.service;


import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;


@Service
@Slf4j

public class TraineeService {
    private final RestService restService;
    private final MinioService minioService;
    private final String voxelUri;

    public TraineeService(RestService restService,
                          MinioService minioService,
                          @Value("${voxelizator.endpoint}") String voxelUri) {
        this.restService = restService;
        this.minioService = minioService;
        this.voxelUri = voxelUri;
    }

    public String executeTrainee(String objectName) {
        if (minioService.objectExists(objectName)) {
            String voxelizedCloud = getVoxelizedCloud(objectName);
        }
        return "";
    }

    private String getVoxelizedCloud(String objectName) {
        log.info("Начало отправки POST запроса на Voxelizator микросервис");
        ParameterizedTypeReference<String> typeRef =
                new ParameterizedTypeReference<>() {};
        String result = restService.post(voxelUri, objectName, typeRef);
        //validateResult(result);
        return result;
    }
}
